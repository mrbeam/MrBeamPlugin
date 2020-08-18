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

def get_thread(callback=None, logname=None, daemon=False, *th_a, **th_kw):
	"""
	returns a function that threads an other function and running a callback if provided.
	Returns the started thread object.
	It also logs any Exceptions that happen in that function.
	see https://gist.github.com/awesomebytes/0483e65e0884f05fb95e314c4f2b3db8
	See https://stackoverflow.com/questions/14234547/threads-with-decorators
	"""
	from .log import logExceptions
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

				t = threading.Thread(target=do_callback, args=a, kwargs=kw, *th_a, **th_kw)
			else:
				logged_f = logExceptions(f)
				t = threading.Thread(target=logged_f, args=a, kwargs=kw)
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

def force_kwargs(**defaultKwargs):
	"""Assigns default kwarg values if they are not *strictly* defined.
	Be careful to use *args as well when defining the function.
	Only necessary for python2.

	```
	@force_kwargs(b=-3)
	def g(a, *args, **kwargs):
	  print("a %s, b %s, args %s, kwargs %s" % (a, b, args, kwargs))

	g(1, 2, 3) # a 1, args (2,3), kwargs {'b': -3}
	g(1, 2, b=3) # a 1, args(2,), kwargs {'b': 3 }

	@force_kwargs(b=-3)
	def f(a, b=None, *args, **kwargs):
	  print("a %s, b %s, args %s, kwargs %s" % (a, b, args, kwargs))

	f(1, 2, 3) # a 1, b -3, args (2,3), kwargs {}
	f(1, 2, b=3) # a 1, b 3, args(2,), kwargs {}

	```

	In Python3, this can be overcome with:

	```
	def f(a, *args, b=-3, **kwargs):
	  print("a %s, b %s, args %s, kwargs %s" % (a, b, args, kwargs))

	f(1, 2, 3) # a 1, b -3, args (2,3), kwargs {}
	f(1, 2, c=5, b=3) # a 1, b 3, args(2,), kwargs {'c': 5}
	```

	@see: https://stackoverflow.com/a/50107777/11136955
	"""
	def decorator(f):
		@wraps(f)
		def g(*args, **kwargs):
			new_args = {}
			varnames = f.__code__.co_varnames
			for k, v in defaultKwargs.items():
				if k in varnames:
					i = varnames.index(k)
					if i >= f.__code__.co_argcount:
						# named same as args or kwargs as in f(a, *args, **kwargs)
						# So it must go into kwargs if not already defined
						if not k in kwargs.keys():
							kwargs[k] = v
					elif k in kwargs.keys():
						new_args[i] = kwargs.pop(k)

					else:
						new_args[i] = defaultKwargs[k]
				elif not k in kwargs.keys():
					kwargs[k] = v
			# Insert new_args into the correct position of the args.
			full_args = list(args)
			for i in sorted(new_args.keys()):
				full_args.insert(i, new_args[i])
			# print("\n\nforce kwargs " + f.__name__ + ", args " + str(full_args) + ", final_kwargs " + str(kwargs) +'\n\n')
			return f(*tuple(full_args), **kwargs)
		return g
	return decorator
