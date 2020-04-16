try:
	import picamera
	Err = picamera.exc.PiCameraError
	MMALErr = picamera.exc.PiCameraMMALError
except ImportError, OSError:
	Err = Exception
	MMALErr = Exception

class CameraException(Err):
	pass

class CameraConnectionException(MMALErr, Err):
	def __init__(self, status, prefix=""):
		MMALErr.__init__(self, status)
	pass