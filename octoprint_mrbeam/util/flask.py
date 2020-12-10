#!/usr/bin/env python3

from __future__ import absolute_import
import functools
from flask import abort
from octoprint.server.util.flask import restricted_access, make_response


def _identity(x):
    return x


def restricted_access_if(condition=False):
    """
    This uses :py:func:`octoprint.server.util.flask.restricted_access` if ``condition`` is met.
    """
    if condition:
        return restricted_access
    else:
        return _identity


def restricted_unless_calibration_tool_mode(func):
    """
    2nd order decorator that checks if ``self`` is a ``MrBeamPlugin`` object
    and is in calibration tool mode. It will restrict access if not.

    See ``octoprint_mrbeam.util.flask.restricted_access_if``
    """

    @functools.wraps(func)
    def decorated_view(cls_obj, *args, **kwargs):
        return restricted_access_if(not cls_obj.calibration_tool_mode)(func)(
            cls_obj, *args, **kwargs
        )

    return decorated_view


def calibration_tool_mode_only(func):
    """
    Only allows access if in calibration tool mode.
    Aborts with 404 otherwise
    """

    @functools.wraps(func)
    def decorated_view(cls_obj, *args, **kwargs):
        if cls_obj and cls_obj.calibration_tool_mode:
            return func(cls_obj, *args, **kwargs)
        else:
            abort(404)
            # return make_response("Not Found", 404)

    return decorated_view
