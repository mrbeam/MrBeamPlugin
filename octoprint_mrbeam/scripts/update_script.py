from __future__ import absolute_import, division, print_function

import base64
import logging
import os
import re
import subprocess
import sys

import yaml
from octoprint.plugins.softwareupdate import exceptions, version_checks
from octoprint.plugins.softwareupdate.updaters.pip import _get_pip_caller

from octoprint.settings import _default_basedir
from requests import ConnectionError
from requests.adapters import HTTPAdapter, Retry
from urllib3.exceptions import MaxRetryError

# _logger = logging.getLogger("octoprint.plugins.mrbeam.softwareupdate.updatescript")
_logger = logging


def parse_arguments():
    import argparse

    boolean_trues = ["true", "yes", "1"]

    parser = argparse.ArgumentParser(prog="update_script.py")

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
        "--call",
        action="store",
        type=lambda x: x in boolean_trues,
        dest="call",
        default=False,
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


def get_dependencies(path):
    dependencies_path = os.path.join(path, "dependencies.txt")
    dependencies_pattern = r"([a-z]+(?:[_-][a-z]+)*)(.=)+([0-9]+.[0-9]+.[0-9]+)"
    try:
        with open(dependencies_path, "r") as f:
            dependencies_content = f.read()
            dependencies_content = re.sub(
                r"[^\S\r\n]", "", dependencies_content
            )  # TODO mabye replace by unittesting the dependencies.txt file
            dependencies = re.findall(dependencies_pattern, dependencies_content)
            dependencies = [{"name": dep[0], "version": dep[2]} for dep in dependencies]
    except IOError:
        raise RuntimeError("Could not load dependencies")
    return dependencies


def get_update_info():
    # TODO test additional exceptions \00 as null char
    update_info_path = os.path.join(_default_basedir("OctoPrint"), "update_info.json")
    try:
        with open(update_info_path, "r") as f:
            # print("file", f.read())
            update_info = yaml.safe_load(f)
    except IOError:
        raise RuntimeError("Could not load update info")
    except ValueError:
        raise RuntimeError("update info not valid json")
    return update_info


# TODO move to util an refactor cloud config part to use same
def get_file_of_repo_for_tag(file, repo, tag):
    """
    return the software update config of the given tag on the repository
    Args:
        tag: tagname
    Returns:
        software update config
    """
    import requests
    import json

    try:
        url = "https://api.github.com/repos/mrbeam/{repo}/contents/{file}?ref={tag}".format(
            repo=repo, file=file, tag=str(tag)
        )

        headers = {
            "Accept": "application/json",
        }

        s = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.3)
        adapter = HTTPAdapter(max_retries=retry)
        s.mount("https://", adapter)
        s.keep_alive = False

        response = s.request("GET", url, headers=headers)
    except MaxRetryError:
        _logger.warning("timeout while trying to get the  file")
        return None
    except ConnectionError:
        _logger.warning("connection error while trying to get the  file")
        return None

    if response:
        json_data = json.loads(response.text)
        content = base64.b64decode(json_data["content"])

        return content
    else:
        _logger.warning("no valid response for the file - %s", response)
        return None


def build_wheels(queue):
    for venv, packages in queue.items():

        pip_caller = _get_pip_caller(command=venv)
        if pip_caller is None:
            raise exceptions.UpdateError("Can't run pip", None)

        def _log_call(*lines):
            _log(lines, prefix=" ", stream="call")

        def _log_stdout(*lines):
            _log(lines, prefix=">", stream="stdout")

        def _log_stderr(*lines):
            _log(lines, prefix="!", stream="stderr")

        def _log(lines, prefix=None, stream=None, strip=True):
            if strip:
                lines = map(lambda x: x.strip(), lines)
            for line in lines:
                print(u"{} {}".format(prefix, line))
                _logger.debug(u"{} {}".format(prefix, line))

        if _logger is not None:
            pip_caller.on_log_call = _log_call
            pip_caller.on_log_stdout = _log_stdout
            pip_caller.on_log_stderr = _log_stderr

        # TODO check arguemtns will work with legacy image pip version
        pip_args = [
            "wheel",
            "--no-python-version-warning",
            "--disable-pip-version-check",
            "--wheel-dir=/tmp/wheelhouse",
            # Build wheels into <dir>, where the default is the current working directory.
            "--no-dependencies",  # Don't install package dependencies.
        ]
        for package in packages:
            if package.get("archive"):
                pip_args.append(package.get("archive"))
            else:
                raise exceptions.UpdateError(
                    "Archive not found for package {}".format(package)
                )

        returncode, stdout, stderr = pip_caller.execute(*pip_args)
        if returncode != 0:
            raise exceptions.UpdateError(
                "Error while executing pip wheel", (stdout, stderr)
            )


# TODO fix for mrbeam plugin commit hash package_version is not target
def install_wheels(queue):
    for venv, packages in queue.items():

        pip_caller = _get_pip_caller(command=venv)
        if pip_caller is None:
            raise exceptions.UpdateError("Can't run pip", None)

        def _log_call(*lines):
            _log(lines, prefix=" ", stream="call")

        def _log_stdout(*lines):
            _log(lines, prefix=">", stream="stdout")

        def _log_stderr(*lines):
            _log(lines, prefix="!", stream="stderr")

        def _log(lines, prefix=None, stream=None, strip=True):
            if strip:
                lines = map(lambda x: x.strip(), lines)
            for line in lines:
                print(u"{} {}".format(prefix, line))
                _logger.debug(u"{} {}".format(prefix, line))

        if _logger is not None:
            pip_caller.on_log_call = _log_call
            pip_caller.on_log_stdout = _log_stdout
            pip_caller.on_log_stderr = _log_stderr

        pip_args = [
            "install",
            "--no-python-version-warning",
            "--disable-pip-version-check",
            "--upgrade"  # Upgrade all specified packages to the newest available version. The handling of dependencies depends on the upgrade-strategy used.
            "--no-index",  # Ignore package index (only looking at --find-links URLs instead).
            "--find-links=/tmp/wheelhouse",
            # If a URL or path to an html file, then parse for links to archives such as sdist (.tar.gz) or wheel (.whl) files. If a local path or file:// URL that's a directory, then look for archives in the directory listing. Links to VCS project URLs are not supported.
            "--no-dependencies",  # Don't install package dependencies.
        ]
        for package in packages:
            pip_args.append(
                "{package}=={package_version}".format(
                    package=package["name"], package_version=package["target"]
                )
            )

        returncode, stdout, stderr = pip_caller.execute(*pip_args)
        if returncode != 0:
            raise exceptions.UpdateError(
                "Error while executing pip install", (stdout, stderr)
            )


def do_update():
    # curl "https://api.github.com/repos/mrbeam/OctoPrint/releases/latest" | yq ".tag_name" -
    # wget https://github.com/{username}/{projectname}/archive/{sha}.zip
    # pip    wheel[project1].zip[project2].zip
    # my/venv/bin/pip install [project1].whl

    args = parse_arguments()

    # get dependencies
    dependencies = get_dependencies(args.folder)

    # get update config of dependencies
    update_info = get_update_info()

    """
        {
        "venv_path": [
                {
                    "name": "packagename"
                    "archive": "archive path"
                    "target": "v01.2.5/#123123"
                }
            ]
        }
    """
    install_queue = {}

    install_queue.setdefault(
        update_info.get("mrbeam").get("pip_command", "/home/pi/oprint/bin/pip"), []
    ).append(
        {
            "name": update_info.get("mrbeam").get("repo"),
            "archive": update_info.get("mrbeam")
            .get("pip")
            .format(target_version=args.target),
            "target": args.target,
        }
    )

    print("dependencies.txt", dependencies)
    # self._plugin_manager.plugins.[softwareupdate].get_current_versions()
    if dependencies:
        for dependency in dependencies:
            mrbeam_config = update_info.get("mrbeam")
            mrbeam_dependencies_config = mrbeam_config.get("dependencies")
            dependency_config = mrbeam_dependencies_config.get(dependency["name"])

            # fail if requirements file contains dependencies but cloud config not
            if dependency_config == None:
                raise exceptions.UpdateError(
                    "no update info for dependency {}".format(dependency["name"])
                )
            print(dependency["name"], dependency_config)  # TODO only debug
            if dependency_config.get("pip"):
                archive = dependency_config["pip"].format(
                    repo=dependency_config["repo"],
                    user=dependency_config["user"],
                    target_version="v{version}".format(version=dependency["version"]),
                )
            else:
                raise exceptions.UpdateError(
                    "pip not configured for {}".format(dependency["name"])
                )
            # TODO check if version is already installed
            install_queue.setdefault(
                dependency_config.get("pip_command", "/home/pi/oprint/bin/pip"), []
            ).append(
                {
                    "name": dependency["name"],
                    "archive": archive,
                    "target": dependency["version"],
                }
            )

    print("install_queue", install_queue)  # TODO only for debug
    build_wheels(install_queue)
    install_wheels(install_queue)


def main():
    _logger.error("test logger")

    args = parse_arguments()
    if args.call:
        do_update()
    else:

        folder = args.folder

        import os

        if not os.access(folder, os.W_OK):
            raise RuntimeError("Could not update, base folder is not writable")

        # dependencies = get_file_of_repo_for_tag(
        #     "octoprint_mrbeam/dependencies.txt",
        #     "MrBeamPlugin",
        #     "feature/SW-649-create-update-script-for-mrbeam-plugin",
        # )
        # TODO ony for debug
        with open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "../dependencies.txt"
            ),
            "r",
        ) as f:
            dependencies = f.read()
        with open(os.path.join(folder, "dependencies.txt"), "w") as f:
            f.write(dependencies)

        new_update_script_path = os.path.join(folder, "update_script_file.py")
        # update_script_file = get_file_of_repo_for_tag(
        #     "octoprint_mrbeam/scripts/update_script.py",
        #     "MrBeamPlugin",
        #     "feature/SW-649-create-update-script-for-mrbeam-plugin",
        # )
        # TODO only for debug
        with open(os.path.abspath(__file__), "r") as f:
            update_script_file = f.read()

        with open(new_update_script_path, "w") as f:
            f.write(update_script_file)

        # call new update script with args
        sys.argv = ["--call=true"] + sys.argv[1:]
        subprocess.call([sys.executable, new_update_script_path] + sys.argv)

        # TODO only for testing
        raise RuntimeError("TEST - Could not update")


if __name__ == "__main__":
    main()
