try:
    from picamera.exc import PiCameraError as _Exc
    from picamera.exc import PiCameraMMALError as _ConnErr
except ImportError, OSError:
    import logging

    logging.warning("Could not import picamera")
    _Exc = Exception
    _ConnErr = Exception

CameraException = _Exc
CameraConnectionException = _ConnErr

CAM_CONN = "err_cam_conn"
CAM_CONNRECOVER = "cam_conn_recover"


class MrbCameraError(CameraException):
    pass


def msg(status):
    return {
        CAM_CONN: "Camera connection error",
        CAM_CONNRECOVER: "Managed to recover from the previous camera error",
    }.get(status, "Unknown status error")


def msgForAnalytics(status):
    return {"message": msg(status), "id": status}
