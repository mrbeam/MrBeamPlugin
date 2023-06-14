try:
    from picamera.exc import PiCameraError as _Exc
    from picamera.exc import PiCameraMMALError as _ConnErr
    from picamera.exc import PiCameraValueError as _ValueErr
    from picamera.exc import PiCameraRuntimeError as _RuntimeErr
except ImportError, OSError:
    import logging

    logging.warning("Could not import picamera")
    _Exc = Exception
    _ConnErr = Exception
    _ValueErr = Exception
    _RuntimeErr = Exception

CameraException = _Exc
CameraConnectionException = _ConnErr
CameraValueException = _ValueErr
CameraRuntimeException = _RuntimeErr

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
