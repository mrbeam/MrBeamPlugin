#!/usr/bin/env python3

from __future__ import absolute_import
import functools
from flask import abort
from octoprint.server.util.flask import restricted_access, make_response


def _identity(x):
    return x


def wrap_if(condition=False, decorator=_identity):
    """
    Run a decorator function` if ``condition`` is met.
    """
    if condition:
        return decorator
    else:
        return _identity


def abort_if(condition=False, code=401):
    """I suspect ``abort`` raises an Exception, in which case this works better."""

    def wrap(f):
        def puppet(*a, **kw):
            return abort(code)

        return puppet

    return wrap_if(condition, decorator=wrap)


def calibration_tool_mode_only(func):
    @functools.wraps(func)
    def decorated_view(cls_obj, *args, **kwargs):
        return abort_if(not cls_obj.calibration_tool_mode)(func)(
            cls_obj, *args, **kwargs
        )

    return decorated_view


def restricted_access_if(condition=False):
    """
    This uses :py:func:`octoprint.server.util.flask.restricted_access` if ``condition`` is met.
    """
    if condition:
        return restricted_access
    else:
        return _identity


def restricted_access_or_calibration_tool_mode(func):
    @functools.wraps(func)
    def decorated_view(cls_obj, *args, **kwargs):
        return restricted_access_if(not cls_obj.calibration_tool_mode)(func)(
            cls_obj, *args, **kwargs
        )

    return decorated_view
