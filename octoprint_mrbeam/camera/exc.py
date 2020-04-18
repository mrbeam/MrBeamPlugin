try:
	import picamera.exc.PiCameraError as _Exc
	import picamera.exc.PiCameraMMALError as _ConnErr
except ImportError, OSError:
	_Exc = Exception
	_ConnErr = Exception

CameraException = _Exc
CameraConnectionException = _ConnErr

(CAM_CONN,
 CAM_CONNRECOVER,
 ) = range(2)

def msg(status):
	return {CAM_CONN:        "Camera connection error",
	        CAM_CONNRECOVER: "Managed to recover from the previous camera error",
            }.get(status, "Unknown status error")

def formatForAnalytics(status, count=1):
	return {status: {'msg': msg(status),
	                 'count': count}}