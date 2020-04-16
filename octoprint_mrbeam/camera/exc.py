try:
	import picamera.exc.PiCameraError as _Exc
	import picamera.exc.PiCameraMMALError as _ConnErr
except ImportError, OSError:
	_Exc = Exception
	_ConnErr = Exception

CameraException = _Exc
CameraConnectionException = _ConnErr
