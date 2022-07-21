FROM ubuntu:21.10

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
    && sudo apt-get install libncursesw5-dev libssl-dev tk-dev libgdbm-dev libc6-dev libbz2-dev -y \
    && sudo apt-get install wget git -y \
    && cd ~/ \
    && wget -O ~/Python-2.7.18.tgz https://www.python.org/ftp/python/2.7.18/Python-2.7.18.tgz \
    && tar xzf Python-2.7.18.tgz \
    && rm Python-2.7.18.tgz \
    && cd ~/Python-2.7.18 \
    && sudo ./configure --enable-optimizations --prefix=/home/mrbeam/ \
    && sudo make install \
    && cd ~/ \
    && wget -O ~/get-pip.py https://bootstrap.pypa.io/pip/2.7/get-pip.py \
    && sudo env "PATH=$PATH" python get-pip.py \
    && sudo env "PATH=$PATH" python -m pip install --upgrade pip \
    && pip install virtualenv \
    && virtualenv --python=python venv2

RUN source ./venv2/bin/activate \
    && git clone https://github.com/mrbeam/OctoPrint.git \
    && cd OctoPrint \
    && git checkout mrbeam2-stable \
    && pip install .

RUN source ./venv2/bin/activate \
    && git clone https://github.com/mrbeam/MrBeamDoc.git \
    && cd MrBeamDoc \
    && git checkout stable \
    && pip install .

RUN source ./venv2/bin/activate \
    && pip install opencv-python==4.2.0.32

COPY --chown=mrbeam ./docker-octoprint-config.yaml /home/mrbeam/.octoprint/config.yaml

COPY --chown=mrbeam docker-beamos_version /etc/beamos_version

COPY --chown=mrbeam . /home/mrbeam/MrBeamPlugin/

RUN source ./venv2/bin/activate \
    && pip install ./MrBeamPlugin

CMD [ "./venv2/bin/python", "-m", "octoprint", "serve", "--port", "5000" ]

HEALTHCHECK  --interval=30s --timeout=3s \
    CMD wget --no-verbose --tries=3 --spider http://localhost:5000 || exit 1
