#!/usr/bin/env python3
from __future__ import absolute_import, print_function, unicode_literals, division
import time
from collections import Mapping
import numpy as np
import json
import logging
from octoprint_mrbeam.mrb_logger import mrb_logger
import sys
from functools import wraps


def logtime(logger=None):
    def _logtime(f):
        @wraps(f)
        def timed_f(*args, **kw):
            start = time.clock()
            ret = f(*args, **kw)
            debug_logger(f).debug("Elapsed time : %f seconds", time.clock() - start)
            return ret

        return timed_f

    return _logtime


def logExceptions(f):
    @wraps(f)
    def wrap(*args, **kw):
        try:
            return f(*args, **kw)
        except Exception as e:
            debug_logger(f).exception(
                "Log exception: %s, %s" % (e.__class__.__name__, e)
            )
            raise

    return wrap


def json_serialisor(elm):
    """Attempts to return a serialisable element if the given one is not."""
    if elm is None or isinstance(elm, (bool, int, float, str, list, tuple, dict)):
        # These types are already supported
        return elm
    elif isinstance(elm, np.ndarray):
        # convert the array elements into serialisable stuff, and change the array to nested lists
        shape = elm.shape
        if not shape:
            # Single element
            return elm.tolist()
        else:  # max(shape) < 10:
            _e = elm.reshape((np.prod(shape),))
            _e = np.asarray(map(json_serialisor, _e))
            return _e.reshape(shape).tolist()
        # else:
        #     return "numpy array with shape %s and type %s " % (elm.shape, elm.dtype)
    else:
        try:
            json.dumps(elm)
            return elm
        except TypeError:
            if "__str__" in dir(elm) or "tostring" in dir(elm):
                return str(elm)
            elif "__repr__" in dir(elm):
                return repr(elm)
            else:
                return "Not JSON serialisable type : {}".format(type(elm))


def log_output(logger, ret):
    logger.debug("output:\n%s" % json.dumps(ret, indent=2, default=json_serialisor))


def log_input(logger, *a, **kw):
    argStr = json.dumps(a, indent=2, default=json_serialisor)
    kwStr = json.dumps(kw, indent=2, default=json_serialisor)
    logger.debug("\narg: %s\nkwargs: %s" % (argStr, kwStr))


def logme(input=False, output=False):
    def decorator(f):
        logger = debug_logger(f)

        @wraps(f)
        def wrapped(*a, **kw):
            if input:
                log_input(logger, *a, **kw)
            ret = f(*a, **kw)
            if output:
                log_output(logger, ret)
            return ret

        return wrapped

    return decorator


def debug_logger(function=None):
    getLogger = mrb_logger
    if function is None:
        logger = getLogger("debug logger")
    elif sys.version_info >= (3, 3):
        # Python version >= 3.3
        logger = getLogger(function.__qualname__)
    else:
        if function.__module__ is None:
            logger = getLogger(function.__name__)
        else:
            logger = getLogger(function.__module__ + "." + function.__name__)
    logger.setLevel(logging.DEBUG)
    return logger
