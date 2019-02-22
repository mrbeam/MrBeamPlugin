
from octoprint_mrbeam.mrb_logger import mrb_logger
from cmd_exec import exec_cmd_output

_logger = mrb_logger("octoprint.plugins.mrbeam.cmd_exec")


def get_version_of_pip_module(pip_name, pip_command=None):
	version = None
	if pip_command is None: pip_command = "pip"
	command = "{pip_command} freeze".format(pip_command=pip_command)
	output, returncode = exec_cmd_output(command, shell=True)
	if returncode == 0:
		lines = output.splitlines()
		for myLine in lines:
			token = myLine.split("==")
			if len(token) >= 2 and token[0] == pip_name:
				if token[1][:1] == "=":
					version = token[1][1:]
				else:
					version = token[1]
				break
		_logger.debug("get_version_of_pip_module() version of pip module '%s' is '%s' (pip command '%s' returned %s)",
						pip_name, version, pip_command, returncode)
	return version
