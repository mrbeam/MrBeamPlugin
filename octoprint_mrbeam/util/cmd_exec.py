
import logging
import subprocess
from octoprint_mrbeam.mrb_logger import mrb_logger


_logger = mrb_logger("octoprint.plugins.mrbeam.cmd_exec")

def exec_cmd(cmd, shell=True):
	'''
	Executes a system command
	:param cmd:
	:return: True if system returncode was 0,
			 False if the command returned with an error,
			 None if there was an exception.
	'''
	code = None

	_logger.debug("_execute_command() command: '%s'", cmd)
	try:
		code = subprocess.call(cmd, shell=shell)
	except Exception as e:
		_logger.debug("Failed to execute command '%s', return code: %s, Exception: %s", cmd, code, e)
		return None

	_logger.debug("_execute_command() command return code: '%s'", code)
	return code == 0


def exec_cmd_output(cmd, log_cmd=True, shell=False):
	'''
	Executes a system command and returns its output.
	:param cmd:
	:return: Tuple(String:output , int return_code)
	'''

	output = None
	code = 0
	if log_cmd:
		_logger.debug("_execute_command() command: '%s'", cmd)
	try:
		output = subprocess.check_output(cmd, shell=shell, stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as e:
		code = e.returncode

		if log_cmd == False and cmd is not None:
			cmd = cmd[:50]+'...' if len(cmd)>30 else cmd

		output = e.output
		# if log_cmd == False and e.output is not None:
		# 	output = e.output[:30]+'...' if len(e.output)>30 else e.output
		_logger.debug("Fail to execute command '%s', return code: %s, output: '%s'", cmd, e.returncode, output)

	return output, code
