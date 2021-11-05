from __future__ import absolute_import, division, print_function


import errno
import subprocess
import sys
import traceback
import time


def parse_arguments():
    import argparse

    boolean_trues = ["true", "yes", "1"]

    parser = argparse.ArgumentParser(prog="update-octoprint.py")

    parser.add_argument(
        "--git",
        action="store",
        type=str,
        dest="git_executable",
        help="Specify git executable to use",
    )
    parser.add_argument(
        "--python",
        action="store",
        type=str,
        dest="python_executable",
        help="Specify python executable to use",
    )
    parser.add_argument(
        "--force",
        action="store",
        type=lambda x: x in boolean_trues,
        dest="force",
        default=False,
        help="Set this to true to force the update to only the specified version (nothing newer, nothing older)",
    )
    parser.add_argument(
        "--sudo", action="store_true", dest="sudo", help="Install with sudo"
    )
    parser.add_argument(
        "--user",
        action="store_true",
        dest="user",
        help="Install to the user site directory instead of the general site directory",
    )
    parser.add_argument(
        "--branch",
        action="store",
        type=str,
        dest="branch",
        default=None,
        help="Specify the branch to make sure is checked out",
    )
    parser.add_argument(
        "folder",
        type=str,
        help="Specify the base folder of the OctoPrint installation to update",
    )
    parser.add_argument(
        "target", type=str, help="Specify the commit or tag to which to update"
    )

    args = parser.parse_args()

    return args


def get_tag_of_bitbucket_repo(repo):
    import requests
    import json

    url = (
        "https://api.bitbucket.org/2.0/repositories/mrbeam/"
        + repo
        + "/refs/tags?sort=-name"
    )

    headers = {
        "Accept": "application/json",
        "Authorization": "Basic TXJCZWFtRGV2OnYyVDVwRmttZGdEcWJGQkpBcXJ0",
    }

    response = requests.request("GET", url, headers=headers)
    json_data = json.loads(response.text)
    return json_data.get("values")[0].get("name")


def main():
    args = parse_arguments()
    print("args", args)
    git_executable = None
    # if args.git_executable:
    #     git_executable = args.git_executable
    #
    # python_executable = sys.executable
    # if args.python_executable:
    #     python_executable = args.python_executable
    #     if python_executable.startswith('"'):
    #         python_executable = python_executable[1:]
    #     if python_executable.endswith('"'):
    #         python_executable = python_executable[:-1]

    # print("Python executable: {!r}".format(python_executable))

    # /home/pi/oprint/bin/python2 - m pip install https://github.com/Josef-MrBeam/test/archive/refs/heads/main.zip

    # updater = self._get_updater(target, check)
    # if updater is None:
    #     raise exceptions.UnknownUpdateType()

    # update_result = updater.perform_update(target, populated_check, target_version, log_cb=self._log, online=online)
    # git+https://{token}@gitprovider.com/user/project.git@{version}

    get_tag_of_bitbucket_repo("iobeam")

    subprocess.check_call(
        [
            "sudo",
            "/usr/local/iobeam/venv/bin/pip",
            "install",
            "-U",
            "git+ssh://git@bitbucket.org/mrbeam/iobeam.git@{target}".format(
                target=get_tag_of_bitbucket_repo("iobeam")
            ),
            "git+ssh://git@bitbucket.org/mrbeam/mrb_hw_info.git@{target}".format(
                target=get_tag_of_bitbucket_repo("mrb_hw_info")
            ),
        ]
    )
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-U",
            "git+https://github.com/mrbeam/MrBeamPlugin.git@{target}".format(
                target=args.target
            ),
        ]
    )
    raise RuntimeError('TEST - Could not update, "git clean -f" failed with returncode')


if __name__ == "__main__":
    main()
