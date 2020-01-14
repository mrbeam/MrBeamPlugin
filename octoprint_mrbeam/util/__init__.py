import sys
from itertools import chain
import time
import logging

def dict_merge(d1, d2): # (d1: dict, d2: dict):
    for k, v in d1.items():
        if k in d2 and isinstance(v, dict) and isinstance(d2[k], dict):
            d2[k] = dict_merge(d1[k], d2[k])
    return dict(chain(d1.items(), d2.items()))

def logtime(f):
    logger = None
    if sys.version_info >= (3, 3):
        # Python version >= 3.3
        logger = logging.getLogger(f.__qualname__)
    else:
        logger = logging.getLogger(f.__module__ + '.' + f.__name__)
    logger.setLevel(logging.DEBUG)
    def timed_f(*args, **kw):
        start = time.time()
        ret = f(*args, **kw)
        logger.debug("Elapsed time : %f seconds", time.time() - start)
        return ret
    return timed_f
