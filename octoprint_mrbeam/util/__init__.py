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
from octoprint_mrbeam.mrb_logger import mrb_logger

def dict_merge(d1, d2, leaf_operation=None): # (d1: dict, d2: dict):
	"""
	Recursive dictionnary update. Works like dict.update but recurses down to merge all subdirectories.
	Does not require to pickle anything.
	Can associate an operation for superposing leaves.
	If leaf_operation == None, then the leaf of d1 get replaced by the leaf of d2.
	"""
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

def logtime(logger=None):
	"""Decorator - Log the duration of the function"""
	def _logtime(f):
		@wraps(f)
		def timed_f(*args, **kw):
			start = time.clock()
			ret = f(*args, **kw)
			f_logger(f).debug("Elapsed time : %f seconds", time.clock() - start)
			return ret
		return timed_f
	return _logtime

def logExceptions(f):
	"""Decorator : Log and re-raise any exception occurring in the function."""
	@wraps(f)
	def wrap(*args, **kw):
		try:
			return f(*args, **kw)
		except Exception as e:
			f_logger(f).exception("%s, %s" % (e.__class__.__name__, e))
			raise
	return wrap

def json_serialisor(elm):
	"""Attempts to return a (similar) serialisable element if the given one is not."""
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
	"""
	Decorator : Log the input or the output of the function.
	Uses json.dumps to write readable dict and list structures.
	"""
	def decorator(f):
		logger = f_logger(f)
		@wraps(f)
		def wrapped(*a, **kw):
			if input: log_input(logger, *a, **kw)
			ret = f(*a, **kw)
			if output: log_output(logger, ret)
			return ret
		return wrapped
	return decorator

def f_logger(function=None, level=logging.DEBUG):
	"""
	Return a logger object with the qualname of the given function.
	If no function is given, it uses the name of the calling function.
	Example:

	project/my_package.py/
	```
	def f():
	    logger = f_logger()
	    logger.info("from the logger")
	```

	project/main.py
	```
	from my_package import f

	f()
	```

	> my_package.f INFO from the logger
	"""
	getLogger = mrb_logger or logging.getLogger
	if function is None:
		# Use the calling functions name
		logger = getLogger(caller_name())
	elif sys.version_info >= (3, 3):
		# Python version >= 3.3
		logger = getLogger(function.__qualname__)
	else:
		if function.__module__ is None:
			logger = getLogger(function.__name__)
		else:
			logger = getLogger(function.__module__ + '.' + function.__name__)
	logger.setLevel(level)
	return logger

def get_thread(callback=None, logname=None, daemon=False):
	"""
	Returns a function that threads an other function and running a callback if provided.
	Returns the started thread object - It is already started!
	The Exceptions in the target function are logged so that they are not lost due to threading.
	see https://gist.github.com/awesomebytes/0483e65e0884f05fb95e314c4f2b3db8
	See https://stackoverflow.com/questions/14234547/threads-with-decorators
	"""
	def wrapper(f):
		@wraps(f)
		def run(*a, **kw):
			if callback is not None:
				@logExceptions
				@wraps(f)
				def do_callback():
					callback(f(*a, **kw))
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

def caller_name(skip=2):
    """Get a name of a caller in the format module.class.method

       `skip` specifies how many levels of stack to skip while getting caller
       name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

       An empty string is returned if skipped levels exceed stack height
    Thank you anatoly techtonik -- https://stackoverflow.com/a/9812105
    """
    import inspect
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
      return ''
    parentframe = stack[start][0]

    name = []
    module = inspect.getmodule(parentframe)
    # `modname` can be None when frame is executed directly in console
    # TODO(techtonik): consider using __main__
    if module:
        name.append(module.__name__)
    # detect classname
    if 'self' in parentframe.f_locals:
        # I don't know any way to detect call from the object method
        # XXX: there seems to be no way to detect static method call - it will
        #      be just a function call
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append( codename ) # function or a method

    ## Avoid circular refs and frame leaks
    #  https://docs.python.org/2.7/library/inspect.html#the-interpreter-stack
    del parentframe, stack

    return ".".join(name)
