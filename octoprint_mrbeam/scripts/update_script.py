from __future__ import absolute_import, division, print_function

import logging
import os
import re
import subprocess
import sys

import yaml
from octoprint.plugins.softwareupdate import exceptions
from octoprint.plugins.softwareupdate.updaters.pip import _get_pip_caller

from octoprint.settings import _default_basedir

from octoprint_mrbeam.util.github_api import get_file_of_repo_for_tag
from octoprint_mrbeam.util.pip_util import get_version_of_pip_module

# _logger = logging.getLogger("octoprint.plugins.mrbeam.softwareupdate.updatescript")
_logger = logging


def _parse_arguments():
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
    """
    return the dependencies saved in the <path>

    Args:
         path: path to the dependencies.txt file

    Returns:
        list of dependencie dict [{"name", "version"}]
    """
    dependencies_path = os.path.join(path, "dependencies.txt")
    dependencies_pattern = r"([a-z]+(?:[_-][a-z]+)*)(.=)+([0-9]+.[0-9]+.[0-9]+)"
    try:
        with open(dependencies_path, "r") as f:
            dependencies_content = f.read()
            dependencies = re.findall(dependencies_pattern, dependencies_content)
            dependencies = [{"name": dep[0], "version": dep[2]} for dep in dependencies]
    except IOError:
        raise RuntimeError("Could not load dependencies")
    return dependencies


def get_update_info():
    """
    returns the update info saved in the update_info.json file
    """
    update_info_path = os.path.join(_default_basedir("OctoPrint"), "update_info.json")
    try:
        with open(update_info_path, "r") as f:
            update_info = yaml.safe_load(f)
    except IOError:
        raise RuntimeError("Could not load update info")
    except ValueError:
        raise RuntimeError("update info not valid json")
    except yaml.YAMLError as e:
        raise RuntimeError("update info not valid json - {}".format(e))
    return update_info


def build_wheels(queue):
    """
    build the wheels of the packages in the queue

    Args:
        queue: dict of venvs with a list of packages to build the wheels

    Returns:
        None

    """
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
            "wheel",
            "--no-python-version-warning",
            "--disable-pip-version-check",
            "--wheel-dir=/tmp/wheelhouse",  # Build wheels into <dir>, where the default is the current working directory.
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
    """
    installs the wheels in the given venv of the queue

    Args:
        queue: dict of venvs with a list of packages to install

    Returns:
        None
    """
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
            "--upgrade",  # Upgrade all specified packages to the newest available version. The handling of dependencies depends on the upgrade-strategy used.
            "--no-index",  # Ignore package index (only looking at --find-links URLs instead).
            "--find-links=/tmp/wheelhouse",  # If a URL or path to an html file, then parse for links to archives such as sdist (.tar.gz) or wheel (.whl) files. If a local path or file:// URL that's a directory, then look for archives in the directory listing. Links to VCS project URLs are not supported.
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


def build_queue(update_info, dependencies, target):
    """
    build the queue of packages to install

    Args:
        update_info: a dict of informations how to update the packages
        dependencies: a list dicts of dependencies [{"name", "version"}]
        target: target of the Mr Beam Plugin to update to

    Returns:
        install_queue: dict of venvs with a list of package dicts {"<venv path>": [{"name", "archive", "target"}]
    """
    install_queue = {}

    install_queue.setdefault(
        update_info.get("mrbeam").get("pip_command", "/home/pi/oprint/bin/pip"), []
    ).append(
        {
            "name": "Mr_Beam",  # update_info.get("mrbeam").get("repo"),
            "archive": update_info.get("mrbeam")
            .get("pip")
            .format(target_version=target),
            "target": "0.10.3",  # TODO fix he version
        }
    )

    if dependencies:
        for dependency in dependencies:
            mrbeam_config = update_info.get("mrbeam")
            mrbeam_dependencies_config = mrbeam_config.get("dependencies")
            dependency_config = mrbeam_dependencies_config.get(dependency["name"])

            # fail if requirements file contains dependencies but cloud config not
            if dependency_config == None:
                raise exceptions.UpdateError(
                    "no update info for dependency", dependency["name"]
                )
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

            version = get_version_of_pip_module(
                dependency["name"],
                dependency_config.get("pip_command", "/home/pi/oprint/bin/pip"),
            )
            if version != dependency["version"]:
                install_queue.setdefault(
                    dependency_config.get("pip_command", "/home/pi/oprint/bin/pip"), []
                ).append(
                    {
                        "name": dependency["name"],
                        "archive": archive,
                        "target": dependency["version"],
                    }
                )
    return install_queue


def run_update():
    """
    collects the dependencies and the update info, builds the wheels and installs them in the correct venv
    """

    args = _parse_arguments()

    # get dependencies
    dependencies = get_dependencies(args.folder)

    # get update config of dependencies
    update_info = get_update_info()

    install_queue = build_queue(update_info, dependencies, args.target)

    print("install_queue", install_queue)  # TODO only for debug
    if install_queue is not None:
        build_wheels(install_queue)
        install_wheels(install_queue)


def main():
    """
    loads the dependencies.txt and the update_script of the given target and executes the new update_script

    Args:
        target: target of the Mr Beam Plugin to update to
        call: if true executet the update itselfe
    """
    _logger.error("test logger")

    args = _parse_arguments()
    if args.call:
        run_update()
    else:

        folder = args.folder

        import os

        if not os.access(folder, os.W_OK):
            raise RuntimeError("Could not update, base folder is not writable")

        dependencies = get_file_of_repo_for_tag(
            "octoprint_mrbeam/dependencies.txt",
            "MrBeamPlugin",
            args.target,
        )
        # # TODO ony for debug
        # with open(
        #     os.path.join(
        #         os.path.dirname(os.path.abspath(__file__)), "../dependencies.txt"
        #     ),
        #     "r",
        # ) as f:
        #     dependencies = f.read()
        if dependencies is None:
            raise RuntimeError("No dependencies found")
        try:
            with open(os.path.join(folder, "dependencies.txt"), "w") as f:
                f.write(dependencies)
        except IOError:
            raise RuntimeError(
                "could not write {}".format(os.path.join(folder, "dependencies.txt"))
            )

        new_update_script_path = os.path.join(folder, "update_script_file.py")
        update_script_file = get_file_of_repo_for_tag(
            "octoprint_mrbeam/scripts/update_script.py",
            "MrBeamPlugin",
            args.target,
        )
        # TODO only for debug
        # with open(os.path.abspath(__file__), "r") as f:
        #     update_script_file = f.read()

        if update_script_file is None:
            raise RuntimeError("No update_script found")

        try:
            with open(new_update_script_path, "w") as f:
                f.write(update_script_file)
        except IOError:
            raise RuntimeError("could not write {}".format(new_update_script_path))

        # call new update script with args
        sys.argv = ["--call=true"] + sys.argv[1:]
        try:
            result = subprocess.call(
                [sys.executable, new_update_script_path] + sys.argv,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            print(e.output)
            raise RuntimeError("error code %s", (e.returncode, e.output))

        print("result", result)
        if result != 0:
            #     # TODO only for testing
            raise exceptions.UpdateError("TEST - Could not update", result)


if __name__ == "__main__":
    main()
