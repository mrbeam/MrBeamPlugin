import logging
import subprocess
from octoprint_mrbeam.mrb_logger import mrb_logger
from logging import DEBUG


def exec_cmd(cmd, log=True, shell=True, loglvl=DEBUG):
    """
    Executes a system command
    :param cmd:
    :return: True if system returncode was 0,
                     False if the command returned with an error,
                     None if there was an exception.
    """
    _logger = mrb_logger(__name__ + ".exec_cmd")
    code = None
    if log:
        _logger.log(loglvl, "cmd=%s", cmd)
    try:
        code = subprocess.call(cmd, shell=shell)
    except Exception as e:
        _logger.error(
            "Failed to execute command '%s', return code: %s, Exception: %s",
            cmd,
            code,
            e,
        )
        return None
    if code != 0 and log:
        _logger.error("cmd= '{}', return code: {}".format(cmd, code))
    return code == 0


def exec_cmd_output(cmd, log=True, shell=False, loglvl=DEBUG):
    """
    Executes a system command and returns its output.
    :param cmd:
    :return: Tuple(String:output , int return_code)
    """
    _logger = mrb_logger(__name__ + "exec_cmd_output")
    output = None
    code = 0
    if log:
        _logger.log(loglvl, "cmd='%s'", cmd)
    try:
        output = subprocess.check_output(cmd, shell=shell, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        code = e.returncode

        if not log:
            cmd = cmd[:50] + "..." if len(cmd) > 30 else cmd
            if e.output is not None:
                output = e.output[:30] + "..." if len(e.output) > 30 else e.output
        else:
            output = e.output
        _logger.log(
            loglvl,
            "Failed to execute command '%s', return code: %s, output: '%s'",
            cmd,
            e.returncode,
            output,
        )

    except Exception as e:
        code = 99
        output = "{e}: {o}".format(e=e, o=output)
        _logger.log(
            loglvl,
            "Failed to execute command '%s', return code: %s, output: '%s'",
            cmd,
            None,
            output,
        )

    return output, code
