
from octoprint_mrbeam.mrb_logger import mrb_logger
from cmd_exec import exec_cmd_output

_logger = mrb_logger("octoprint.plugins.mrbeam.pip_util")

_freezes={}

def get_version_of_pip_module(pip_name, pip_command=None):
	global _freezes
	version = None
	returncode = -1
	if pip_command is None: pip_command = "pip"
	my_freeze = _freezes.get(pip_command, None)

	if my_freeze is None:
		command = "{pip_command} freeze".format(pip_command=pip_command)
		_logger.debug("get_version_of_pip_module() executing pip command: '%s'", pip_command)
		output, returncode = exec_cmd_output(command, shell=True)
		if returncode == 0:
			my_freeze = output.splitlines()
			_freezes[pip_command] = my_freeze
		else:
			_logger.warn("get_version_of_pip_module() pip command '%s' returned code %s", pip_command, returncode)

	for myLine in my_freeze:
		token = myLine.split("==")
		if len(token) >= 2 and token[0] == pip_name:
			if token[1][:1] == "=":
				version = token[1][1:]
			else:
				version = token[1]
			break
	_logger.debug("get_version_of_pip_module() version of pip module '%s' is '%s'", pip_name, version)
	return version
