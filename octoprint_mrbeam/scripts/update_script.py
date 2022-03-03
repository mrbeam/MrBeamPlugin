from __future__ import absolute_import, division, print_function


import errno
import json
import os
import re
import subprocess
import sys
import traceback
import time

from octoprint.plugins.softwareupdate import exceptions, version_checks
from octoprint.plugins.softwareupdate.version_checks.github_release import (
    _get_latest_release,
    get_latest,
)


def parse_arguments():
    import argparse

    boolean_trues = ["true", "yes", "1"]

    parser = argparse.ArgumentParser(prog="update-script.py")

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
        "--dependencies",
        action="store",
        type=str,
        default=None,
        help="Specify the dependencies of this plugin",
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


def _get_version_checker(target, check):
    """
    copypasta of octorpint softwareupdate/__init__.py _get_version_checker
    Retrieves the version checker to use for given target and check configuration. Will raise an UnknownCheckType
    if version checker cannot be determined.
    """

    if not "type" in check:
        raise exceptions.ConfigurationInvalid("no check type defined")

    check_type = check["type"]
    method = getattr(version_checks, check_type)
    if method is None:
        raise exceptions.UnknownCheckType()
    else:
        return method


def get_dependencies():
    # TODO fix path
    dependencies_path = os.path.join("", "dependencies.txt")
    dependencies_pattern = re.compile(
        r"([a-z] + (?:_[a-z]+) *)(. =)+([0-9] +.[0-9]+.[0-9]+)/g"
    )
    with open(dependencies_path, "r") as f:
        try:
            dependencies_content = f.read()
            dependencies_content = re.sub(r"\s+", "", dependencies_content)
            dependencies = dependencies_pattern.match(dependencies_content)
        except ValueError:
            raise  # TODO raise execption
    return dependencies


def get_update_info():
    update_info_path = os.path.join(
        self.plugin._settings.getBaseFolder("base"), "update_info.json"
    )
    with open(update_info_path, "r") as f:
        try:
            update_info = json.load(f)
        except ValueError:
            raise  # TODO raise execption
    return update_info


def main():
    # TODO get update script and dependencies of github tag

    update_info = get_update_info()

    # todo get dependencies of dependencies.txt
    dependencies = get_dependencies()
    # TODO fail if requirements file contains dependecies but cloud config not

    # todo build wheels
    # todo install with pip install in correct vevn
    # save commithash to config

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

    # curl "https://api.github.com/repos/mrbeam/OctoPrint/releases/latest" | yq ".tag_name" -
    # wget https://github.com/{username}/{projectname}/archive/{sha}.zip
    # pip    wheel[project1].zip[project2].zip
    # my/venv/bin/pip install [project1].whl
    # print("dependencies", args.dependencies)
    # d = json.loads(args.dependencies)
    # TODO GET plugin and unzip update script, use this as update script

    # TODO GET LATEST TAG OF ALL MODULES
    dependencies = config.get("mrbeam").get("dependencies", None)
    print("dependencies.json", dependencies)
    # self._plugin_manager.plugins.[softwareupdate].get_current_versions()
    if dependencies:
        for dependencie, dependencie_config in dependencies.items():
            print(dependencie, dependencie_config)
            print(get_latest("dependencie", dependencie_config))  # get release
            version_checker = _get_version_checker(dependencie, dependencie_config)
            # print(version_checker)
            information, is_current = version_checker.get_latest(
                dependencie, dependencie_config, True
            )
            print("info", information, is_current)
            if information is not None and not is_current:
                update_available = True

    # TODO WGET ZIP OF ALL MODULES
    # TODO CREATE WHEEL OF ALL MODULES
    # TODO INSTALL ALL WHEELS

    # subprocess.check_call(
    #     [
    #         "sudo",
    #         "/usr/local/iobeam/venv/bin/pip",
    #         "install",
    #         "-U",
    #         "git+ssh://git@bitbucket.org/mrbeam/iobeam.git@{target}".format(
    #             target=get_tag_of_bitbucket_repo("iobeam")
    #         ),
    #         "git+ssh://git@bitbucket.org/mrbeam/mrb_hw_info.git@{target}".format(
    #             target=get_tag_of_bitbucket_repo("mrb_hw_info")
    #         ),
    #     ]
    # )
    # subprocess.check_call(
    #     [
    #         sys.executable,
    #         "-m",
    #         "pip",
    #         "install",
    #         "-U",
    #         "git+https://github.com/mrbeam/MrBeamPlugin.git@{target}".format(
    #             target=args.target
    #         ),
    #     ]
    # )
    raise RuntimeError('TEST - Could not update, "git clean -f" failed with returncode')


if __name__ == "__main__":
    main()
