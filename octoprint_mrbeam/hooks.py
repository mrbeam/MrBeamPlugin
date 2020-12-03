"""
OctoPrint Hooks
See https://docs.octoprint.org/en/master/plugins/hooks.html
See https://docs.octoprint.org/en/ < version > /plugins/hooks.html
"""
from __future__ import absolute_import
from .util.log import logExceptions, logme


@logExceptions
def http_bodysize(current_max_body_sizes, *args, **kwargs):
    """
    Defines the maximum size that is accepted for upload.
    If the uploaded file size exeeds this limit,
    you'll see only a ERR_CONNECTION_RESET in Chrome.
    """
    return [
        ("POST", r"/convert", 100 * 1024 * 1024),
        ("POST", r"/save_store_bought_svg", 100 * 1024 * 1024),
    ]


@logExceptions
@logme(False, True)
def loginui_theming():
    """
    See [here](https://docs.octoprint.org/en/1.4.2/bundledplugins/loginui.html#loginui_theming_hook).
    """
    from flask import url_for
    import logging

    return [url_for("plugin.mrbeam.static", filename="css/loginui.css")]


def filemanager_extensions(*args, **kwargs):
    from octoprint.filemanager import ContentTypeDetector, ContentTypeMapping

    def _image_mime_detector(path):
        p = path.lower()
        if p.endswith(".jpg") or p.endswith(".jpeg") or p.endswith(".jpe"):
            return "image/jpeg"
        elif p.endswith(".png"):
            return "image/png"
        elif p.endswith(".gif"):
            return "image/gif"
        elif p.endswith(".bmp"):
            return "image/bmp"
        elif p.endswith(".pcx"):
            return "image/x-pcx"
        elif p.endswith(".webp"):
            return "image/webp"

    return dict(
        # extensions for image / 3d model files
        model=dict(
            # TODO enable once 3d support is ready
            # stl=ContentTypeMapping(["stl"], "application/sla"),
            image=ContentTypeDetector(
                ["jpg", "jpeg", "jpe", "png", "gif", "bmp", "pcx", "webp"],
                _image_mime_detector,
            ),
            svg=ContentTypeMapping(["svg"], "image/svg+xml"),
            dxf=ContentTypeMapping(["dxf"], "application/dxf"),
        ),
        # .mrb files are svgs, representing the whole working area of a job
        recentjob=dict(
            svg=ContentTypeMapping(["mrb"], "image/svg+xml"),
        ),
        # extensions for printable machine code
        machinecode=dict(
            # already defined by OP: "gcode", "gco", "g"
            gcode=ContentTypeMapping(["nc"], "text/plain")
        ),
    )
