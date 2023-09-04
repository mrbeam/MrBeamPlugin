#!/usr/bin/env python3

import shutil
from os.path import isfile, split, join
from cv2 import imwrite
from .log import logtime

SUCCESS_WRITE_RETVAL = 1

# @logtime()
def differed_imwrite(filename, *a, **kw):
    """Writes to a temporary file before overwriting any file at the given
    path."""
    # This method is being used by the camera plugin
    # Do not modify without checking the usage in the camera plugin

    _path = filename
    while isfile(_path):
        __dir, __f = split(_path)
        _path = join(__dir, "_" + __f)
    res = imwrite(_path, *a, **kw) == SUCCESS_WRITE_RETVAL
    if res and _path != filename:
        shutil.move(_path, filename)
    return res
