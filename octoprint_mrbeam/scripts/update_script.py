from __future__ import absolute_import, division, print_function

import json
import os
import re
import shutil
import subprocess
import sys
from io import BytesIO

import zipfile
import requests
import argparse

from octoprint.plugins.softwareupdate import exceptions

from octoprint.settings import _default_basedir
from octoprint_mrbeam.mrb_logger import mrb_logger

from octoprint_mrbeam.util.pip_util import get_version_of_pip_module, get_pip_caller
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from urllib3.exceptions import MaxRetryError, ConnectionError

_logger = mrb_logger("octoprint.plugins.mrbeam.softwareupdate.updatescript")


UPDATE_CONFIG_NAME = "mrbeam"
REPO_NAME = "MrBeamPlugin"
MAIN_SRC_FOLDER_NAME = "octoprint_mrbeam"
PLUGIN_NAME = "Mr_Beam"
DEFAULT_OPRINT_VENV = "/home/pi/oprint/bin/pip"
PIP_WHEEL_TEMP_FOLDER = "/tmp/wheelhouse"


def _parse_arguments():
    boolean_trues = ["true", "yes", "1"]

    parser = argparse.ArgumentParser(prog=__file__)

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
        help="Calls the update methode",
    )
    parser.add_argument(
        "--archive",
        action="store",
        type=str,
        dest="archive",
        default=None,
        help="Path of target zip file on local system",
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
    dependencies_pattern = r"([a-z]+(?:[_-][a-z]+)*)(.=)+(([1-9][0-9]*!)?(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*((a|b|rc)(0|[1-9][0-9]*))?(\.post(0|[1-9][0-9]*))?(\.dev(0|[1-9][0-9]*))?)"
    """
    Example:
    input:  iobeam==0.7.15
            mrb-hw-info==0.0.25
            mrbeam-ledstrips==0.2.2-alpha.2
    output: [[iobeam][==][0.7.15]]
            [[mrb-hw-info][==][0.0.25]]
            [[mrbeam-ledstrips][==][0.2.2-alpha.2]]        
    """
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
            update_info = json.load(f)
    except IOError:
        raise RuntimeError("Could not load update info")
    except ValueError as e:
        raise RuntimeError("update info not valid json - {}".format(e))
    return update_info


def build_wheels(build_queue):
    """
    build the wheels of the packages in the queue

    Args:
        build_queue: dict of venvs with a list of packages to build the wheels

    Returns:
        None

    """
    try:
        if not os.path.isdir(PIP_WHEEL_TEMP_FOLDER):
            os.mkdir(PIP_WHEEL_TEMP_FOLDER)
    except OSError as e:
        raise RuntimeError("can't create wheel tmp folder {} - {}".format(PIP_WHEEL_TEMP_FOLDER, e))

    for venv, packages in build_queue.items():
        tmp_folder = os.path.join(PIP_WHEEL_TEMP_FOLDER, re.search(r"\w+((?=\/venv)|(?=\/bin))", venv).group(0))
        if os.path.isdir(tmp_folder):
            try:
                os.system("sudo rm -r {}".format(tmp_folder))
            except Exception as e:
                raise RuntimeError("can't delete pip wheel temp folder {} - {}".format(tmp_folder, e))

        pip_args = [
            "wheel",
            "--disable-pip-version-check",
            "--wheel-dir={}".format(tmp_folder),  # Build wheels into <dir>, where the default is the current working directory.
            "--no-dependencies",  # Don't install package dependencies.
        ]
        for package in packages:
            if package.get("archive"):
                pip_args.append(package.get("archive"))
            else:
                raise RuntimeError("Archive not found for package {}".format(package))

        returncode, exec_stdout, exec_stderr = get_pip_caller(venv, _logger).execute(
            *pip_args
        )
        if returncode != 0:
            raise exceptions.UpdateError(
                "Error while executing pip wheel", (exec_stdout, exec_stderr)
            )


def install_wheels(install_queue):
    """
    installs the wheels in the given venv of the queue

    Args:
        install_queue: dict of venvs with a list of packages to install

    Returns:
        None
    """
    if not isinstance(install_queue, dict):
        raise RuntimeError("install queue is not a dict")

    for venv, packages in install_queue.items():
        tmp_folder = os.path.join(PIP_WHEEL_TEMP_FOLDER, re.search(r"\w+((?=\/venv)|(?=\/bin))", venv).group(0))
        pip_args = [
            "install",
            "--disable-pip-version-check",
            "--upgrade",  # Upgrade all specified packages to the newest available version. The handling of dependencies depends on the upgrade-strategy used.
            "--force-reinstall",  # Reinstall all packages even if they are already up-to-date.
            "--no-index",  # Ignore package index (only looking at --find-links URLs instead).
            "--find-links={}".format(tmp_folder),  # If a URL or path to an html file, then parse for links to archives such as sdist (.tar.gz) or wheel (.whl) files. If a local path or file:// URL that's a directory, then look for archives in the directory listing. Links to VCS project URLs are not supported.
            "--no-dependencies",  # Don't install package dependencies.
        ]
        for package in packages:
            pip_args.append(
                "{package}".format(
                    package=package["name"]
                )
            )

        returncode, exec_stdout, exec_stderr = get_pip_caller(venv, _logger).execute(
            *pip_args
        )
        if returncode != 0:
            raise exceptions.UpdateError(
                "Error while executing pip install", (exec_stdout, exec_stderr)
            )


def build_queue(update_info, dependencies, plugin_archive):
    """
    build the queue of packages to install

    Args:
        update_info: a dict of informations how to update the packages
        dependencies: a list dicts of dependencies [{"name", "version"}]
        plugin_archive: path to archive of the plugin

    Returns:
        install_queue: dict of venvs with a list of package dicts {"<venv path>": [{"name", "archive", "target"}]
    """
    install_queue = {}

    install_queue.setdefault(
        update_info.get(UPDATE_CONFIG_NAME).get("pip_command", DEFAULT_OPRINT_VENV), []
    ).append(
        {
            "name": PLUGIN_NAME,
            "archive": plugin_archive,
            "target": '',
        }
    )
    print("dependencies - {}".format(dependencies))
    if dependencies:
        for dependency in dependencies:
            plugin_config = update_info.get(UPDATE_CONFIG_NAME)
            plugin_dependencies_config = plugin_config.get("dependencies")
            dependency_config = plugin_dependencies_config.get(dependency["name"])

            # fail if requirements file contains dependencies but cloud config not
            if dependency_config == None:
                raise RuntimeError(
                    "no update info for dependency {}".format(dependency["name"])
                )

            # override the dependency version from the dependencies files with the one from the cloud config
            if dependency_config.get("version"):
                version_needed = dependency_config.get("version")
            else:
                version_needed = dependency.get("version")

            if dependency_config.get("pip"):
                archive = dependency_config["pip"].format(
                    target_version="v{version}".format(version=version_needed),
                )
            else:
                raise RuntimeError(
                    "pip not configured for {}".format(dependency["name"])
                )

            installed_version = get_version_of_pip_module(
                dependency["name"],
                dependency_config.get("pip_command", DEFAULT_OPRINT_VENV),
            )

            if installed_version != version_needed:
                install_queue.setdefault(
                    dependency_config.get("pip_command", DEFAULT_OPRINT_VENV), []
                ).append(
                    {
                        "name": dependency["name"],
                        "archive": archive,
                        "target": version_needed,
                    }
                )
            else:
                print(
                    "skip dependency {} as the target version {} is already installed".format(
                        dependency["name"], version_needed
                    )
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

    install_queue = build_queue(
        update_info, dependencies, args.archive
    )

    print("install_queue", install_queue)
    if install_queue is not None:
        build_wheels(install_queue)
        install_wheels(install_queue)


def retryget(url, retrys=3, backoff_factor=0.3):
    """
    retrys the get <retrys> times

    Args:
        url: url to access
        retrys: number of retrys
        backoff_factor: factor for time between retrys

    Returns:
        response
    """
    try:
        s = requests.Session()
        retry = Retry(connect=retrys, backoff_factor=backoff_factor)
        adapter = HTTPAdapter(max_retries=retry)
        s.mount("https://", adapter)
        s.keep_alive = False

        response = s.request("GET", url)
        return response
    except MaxRetryError:
        raise RuntimeError("timeout while trying to get {}".format(url))
    except ConnectionError:
        raise RuntimeError("connection error while trying to get {}".format(url))


def loadPluginTarget(archive, folder):
    """
    download the archive of the Plugin and copy dependencies and update script in the working directory

    Args:
        archive: path of the archive to download and unzip
        folder: working directory

    Returns:
        zip_file_path - path of the downloaded zip file
    """

    # download target repo zip
    req = retryget(archive)
    filename = archive.split("/")[-1]
    zip_file_path = os.path.join(folder, filename)
    try:
        with open(zip_file_path, "wb") as output_file:
            output_file.write(req.content)
    except IOError:
        raise RuntimeError(
            "Could not save the zip file to the working directory {}".format(folder)
        )

    # unzip repo
    plugin_extracted_path = os.path.join(folder, UPDATE_CONFIG_NAME)
    plugin_extracted_path_folder = os.path.join(
        plugin_extracted_path,
        "{repo_name}-{target}".format(
            repo_name=REPO_NAME, target=re.sub(r"^v", "", filename.split(".zip")[0])
        ),
    )
    try:
        plugin_zipfile = zipfile.ZipFile(BytesIO(req.content))
        plugin_zipfile.extractall(plugin_extracted_path)
        plugin_zipfile.close()
    except (zipfile.BadZipfile, zipfile.LargeZipFile) as e:
        raise RuntimeError("Could not unzip plugin repo - error: {}".format(e))

    # copy new dependencies to working directory
    try:
        shutil.copy2(
            os.path.join(
                plugin_extracted_path_folder, MAIN_SRC_FOLDER_NAME, "dependencies.txt"
            ),
            os.path.join(folder, "dependencies.txt"),
        )
    except IOError:
        raise RuntimeError("Could not copy dependencies to working directory")

    # copy new update script to working directory
    try:
        shutil.copy2(
            os.path.join(
                plugin_extracted_path_folder,
                MAIN_SRC_FOLDER_NAME,
                "scripts/update_script.py",
            ),
            os.path.join(folder, "update_script.py"),
        )
    except IOError:
        raise RuntimeError("Could not copy update_script to working directory")

    return zip_file_path


def main():
    """
    loads the dependencies.txt and the update_script of the given target and executes the new update_script

    Args:
        target: target of the Mr Beam Plugin to update to
        call: if true executet the update itselfe
    """

    args = _parse_arguments()
    if args.call:
        if args.archive is None:
            raise RuntimeError(
                "Could not run update archive is missing"
            )
        run_update()
    else:

        folder = args.folder

        import os

        if not os.access(folder, os.W_OK):
            raise RuntimeError("Could not update, base folder is not writable")

        update_info = get_update_info()
        archive = loadPluginTarget(
            update_info.get(UPDATE_CONFIG_NAME)
            .get("pip")
            .format(target_version=args.target),
            folder,
        )

        # call new update script with args
        sys.argv = [
            "--call=true",
            "--archive={}".format(archive)
        ] + sys.argv[1:]
        try:
            result = subprocess.call(
                [sys.executable, os.path.join(folder, "update_script.py")] + sys.argv,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            print(e.output)
            raise RuntimeError("error code %s", (e.returncode, e.output))

        if result != 0:
            raise RuntimeError("Error Could not update returncode - {}".format(result))


if __name__ == "__main__":
    main()
