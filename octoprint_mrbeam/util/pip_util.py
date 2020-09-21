from octoprint_mrbeam.mrb_logger import mrb_logger
from cmd_exec import exec_cmd_output

DISABLE_PIP_CHECK = "--disable-pip-version-check"

_freezes = {}


def get_version_of_pip_module(pip_name, pip_command=None, disable_pip_ver_check=True):
    _logger = mrb_logger(__name__ + "get_version_of_pip_module")
    global _freezes
    version = None
    returncode = -1
    if pip_command is None:
        pip_command = "pip"
    elif isinstance(pip_command, list):
        pip_command = " ".join(pip_command)
    if disable_pip_ver_check and not DISABLE_PIP_CHECK in pip_command:
        pip_command += " " + DISABLE_PIP_CHECK
    my_freeze = _freezes.get(pip_command, None)

    if my_freeze is None:
        command = "{pip_command} freeze".format(pip_command=pip_command)
        _logger.debug("refreshing list of installed packages (%s freeze)", pip_command)
        output, returncode = exec_cmd_output(command, shell=True, log=False)
        if returncode == 0:
            my_freeze = output.splitlines()
            _freezes[pip_command] = my_freeze
        elif returncode == 127:
            _logger.error(
                "`%s` was not found in local $PATH (returncode %s)",
                pip_command,
                returncode,
            )
            return None
        else:
            _logger.warning("`%s freeze` returned code %s", pip_command, returncode)
    for myLine in my_freeze:
        token = myLine.split("==")
        if len(token) >= 2 and token[0] == pip_name:
            if token[1][:1] == "=":
                version = token[1][1:]
            else:
                version = token[1]
            break
    _logger.debug("%s==%s", pip_name, version)
    return version
