FROM ubuntu:22.04

ENV TZ=Europe/Berlin
# Installing python and pip on user level so we need to add it to the PATH
ENV PATH="/home/mrbeam/.local/bin:/home/mrbeam/bin:${PATH}"

SHELL ["/bin/bash", "-c"]

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN mkdir /home/mrbeam/ \
    && groupadd -g 999 mrbeam \
    && useradd -r -u 999 -g mrbeam mrbeam \
    && apt-get update \
    && apt-get -y install sudo \
    && adduser mrbeam sudo \
    && echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers \
    && chown mrbeam /home/mrbeam

USER mrbeam

WORKDIR /home/mrbeam

RUN sudo apt-get upgrade -y \
    && sudo apt-get install build-essential -y \
    && sudo apt-get install libncursesw5-dev libssl-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev -y \
    && sudo apt-get install wget git -y \
    && cd ~/ \
    && wget -O ~/Python-3.10.9.tgz https://www.python.org/ftp/python/3.10.9/Python-3.10.9.tgz \
    && tar xzf Python-3.10.9.tgz \
    && rm Python-3.10.9.tgz \
    && cd ~/Python-3.10.9 \
    && sudo ./configure --enable-optimizations --prefix=/home/mrbeam/ \
    && sudo make install \
    && cd ~/ \
    && pip3 install virtualenv \
    && virtualenv --python=python venv3 \
    && sudo apt-get install libffi-dev python3-dev -y

RUN source ./venv3/bin/activate \
    && git clone https://github.com/mrbeam/OctoPrint.git \
    && cd OctoPrint \
    && git checkout feature/SW-1030-octoprint-upgrade-to-latest-v-1-x \
    && pip3 install .

RUN source ./venv3/bin/activate \
    && git clone https://github.com/mrbeam/MrBeamDoc.git \
    && cd MrBeamDoc \
    && git checkout stable \
    && pip3 install .

RUN source ./venv3/bin/activate \
    && pip3 install opencv-python

COPY --chown=mrbeam docker_config/docker-octoprint-config.yaml /home/mrbeam/.octoprint/config.yaml

COPY --chown=mrbeam ./cypress/test_file  /home/mrbeam/.octoprint/uploads/

COPY --chown=mrbeam docker_config/docker-users.yaml /home/mrbeam/.octoprint/users.yaml

COPY --chown=mrbeam docker_config/docker-beamos_version /etc/beamos_version

COPY --chown=mrbeam . /home/mrbeam/MrBeamPlugin/

RUN source ./venv3/bin/activate \
    && pip3 install ./MrBeamPlugin

CMD [ "./venv3/bin/python", "-m", "octoprint", "serve", "--port", "5000" ]

HEALTHCHECK  --interval=30s --timeout=3s \
    CMD wget --no-verbose --tries=3 --spider http://localhost:5000 || exit 1
