import sys
from itertools import chain
import time
import logging
import numpy as np
import json

def dict_merge(d1, d2): # (d1: dict, d2: dict):
	for k, v in d1.items():
		if k in d2 and isinstance(v, dict) and isinstance(d2[k], dict):
			d2[k] = dict_merge(d1[k], d2[k])
	return dict(chain(d1.items(), d2.items()))

def logtime(f):
	logger = debug_logger(f)
	def timed_f(*args, **kw):
		start = time.time()
		ret = f(*args, **kw)
		logger.debug("Elapsed time : %f seconds", time.time() - start)
		return ret
	return timed_f

def json_serialisor(elm):
	"""Attempts to return a serialisable element if the given one is not."""
	if elm is None or type(elm) in [bool, int, float, str, list, tuple, dict]:
		# These types are already supported
		return elm
	elif isinstance(elm, np.ndarray):
		# convert the array elements into serialisable stuff, and change the array to nested lists
		shape = elm.shape
		if max(shape) < 10 :
			_e = elm.reshape((np.prod(shape),))
			_e = np.asarray(map(json_serialisor, _e))
			return _e.reshape(shape).tolist()
		else :
			return "numpy array with shape %s and type %s " % (elm.shape, elm.dtype)
	else:
		try:
			json.dumps(elm)
			return elm
		except TypeError:
			if "__str__" in dir(elm) or 'tostring' in dir(elm):
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
		def wrapped(*a, **kw):
			if input: log_input(logger, *a, **kw)
			ret = f(*a, **kw)
			if output: log_output(logger, ret)
			return ret
		return wrapped
	return decorator

def debug_logger(function=None):
	if function is None:
		logger = logging.getLogger("debug logger")
	elif sys.version_info >= (3, 3):
		# Python version >= 3.3
		logger = logging.getLogger(function.__qualname__)
	else:
		logger = logging.getLogger(function.__module__ + '.' + function.__name__)
	logger.setLevel(logging.DEBUG)
	return logger

