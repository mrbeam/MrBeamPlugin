from octoprint_mrbeam.mrb_logger import mrb_logger
from cmd_exec import exec_cmd_output

DISABLE_PIP_CHECK = "--disable-pip-version-check"
DISABLE_PY_WARNING = "--no-python-version-warning"

# Dictionary of package versions available at different locations
# {
# /home/pi/oprint/bin/pip : {
#   "OctoPrint    x.x.x",
#   ...
#   },
# /usr/share/iobeam/venv/bin/pip : {
#   "iobeam y.y.y",
#   ...
#   }
# }
_pip_package_version_lists = {}


def get_version_of_pip_module(pip_name, pip_command=None, disable_pip_ver_check=True):
    _logger = mrb_logger(__name__ + ".get_version_of_pip_module")
    global _pip_package_version_lists
    version = None
    returncode = -1
    if pip_command is None:
        pip_command = "pip"
    elif isinstance(pip_command, list):
        pip_command = " ".join(pip_command)
    # Checking for pip version outdate takes extra time and text output.
    # NOTE: Older versions of pip do not have the --no-python-version-warning flag
    for disabled in [
        DISABLE_PIP_CHECK,
    ]:  # DISABLE_PY_WARNING]:
        if disable_pip_ver_check and not disabled in pip_command:
            pip_command += " " + disabled
    venv_packages = _pip_package_version_lists.get(pip_command, None)

    if venv_packages is None:
        # perform a pip discovery and remember it for next time
        command = "{pip_command} list".format(pip_command=pip_command)
        _logger.debug("refreshing list of installed packages (%s list)", pip_command)
        output, returncode = exec_cmd_output(command, shell=True, log=False)
        if returncode == 0:
            venv_packages = output.splitlines()
            _pip_package_version_lists[pip_command] = venv_packages
        elif returncode == 127:
            _logger.error(
                "`%s` was not found in local $PATH (returncode %s)",
                pip_command,
                returncode,
            )
            return None
        else:
            _logger.warning("`%s list` returned code %s", pip_command, returncode)
            return None
    # Go through the package list available in our venv
    for line in venv_packages:
        token = line.split()
        if len(token) >= 2 and token[0] == pip_name:
            version = token[1]
            break
    _logger.debug("%s==%s", pip_name, version)
    return version
