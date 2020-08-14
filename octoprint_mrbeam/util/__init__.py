import sys
from itertools import chain
import time
import logging
import numpy as np
import json
from itertools import chain, repeat, cycle
from functools import wraps
from copy import copy
import threading
from .log import logExceptions, logtime

def dict_merge(d1, d2, leaf_operation=None): # (d1: dict, d2: dict):
	"""Recursive dictionnary update.
	Can associate an operation for superposing leaves."""
	if isinstance(d1, dict) and isinstance(d2, dict):
		out = copy(d1)
		for k in set(chain(d1.keys(), d2.keys())):
			if k in d2.keys() and k in d1.keys():
				out[k] = dict_merge(d1[k], d2[k], leaf_operation)
			elif k in d2.keys():
				out[k] = d2[k]
		return out
	elif leaf_operation is not None:
		ret = leaf_operation(d1, d2)
		if ret is None: return d1
		else: return ret
	else:
		return d2

def get_thread(callback=None, logname=None, daemon=False):
	"""
	returns a function that threads an other function and running a callback if provided.
	Returns the started thread object.
	see https://gist.github.com/awesomebytes/0483e65e0884f05fb95e314c4f2b3db8
	See https://stackoverflow.com/questions/14234547/threads-with-decorators
	"""
	def wrapper(f):
		# if logname:
		# 	logger = logging.getLogger(logname)
		# else:
		# 	logger = debug_logger(f)
		@wraps(f)
		def run(*a, **kw):
			if callback is not None:
				@logExceptions
				@wraps(f)
				def do_callback():
					# try:
					callback(f(*a, **kw))
					# except Exception as e:
					# 	logger.exception("E")

				t = threading.Thread(target=do_callback, args=a, kwargs=kw)
			else:
				t = threading.Thread(target=f, args=a, kwargs=kw)
			if daemon:
				t.daemon = True
			t.start()
			return t
		return run
	return wrapper

def makedirs(path, parent=False, *a, **kw):
	"""
	Same as os.makedirs but doesn't throw exception if dir exists
	@param parentif: bool create the parent directory for the path given and not the full path
	                 (avoids having to use os.path.dirname)
	Python >= 3.5 see mkdir(parents=True, exist_ok=True)
	See https://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
	"""
	from os.path import dirname, isdir
	from os import makedirs
	import errno
	if parent:
		_p = dirname(path)
	else:
		_p = path
	try:
		makedirs(_p, *a, **kw)
	except OSError as exc:
		if exc.errno == errno.EEXIST and isdir(_p):
			pass
		else:
			raise
