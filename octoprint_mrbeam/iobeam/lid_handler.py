import logging
import time
import threading
from subprocess import call

from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents


# This guy handles lid Events
# Honestly, I'm not sure if we need a separate handler for this...
class LidHandler(object):

	def __init__(self, iobeam_handler, event_bus, plugin_manager):
		self._iobeam_handler = iobeam_handler
		self._event_bus = event_bus
		self._plugin_manager = plugin_manager
		self._logger = logging.getLogger("octoprint.plugins.mrbeam.iobeam.lidhandler")

		self._photo_creator = PhotoCreator()
		self._worker = None

		self._subscribe()

	def _subscribe(self):
		self._event_bus.subscribe(IoBeamEvents.LID_OPENED, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.LID_CLOSED, self.onEvent)

	def onEvent(self, event, payload):
		if event == IoBeamEvents.LID_OPENED:
			self._worker = threading.Thread(target=self._photo_creator.work)
			self._worker.daemon = True
			self._worker.start()
		elif event == IoBeamEvents.LID_CLOSED:
			self._photo_creator.active = False


class PhotoCreator(object):

	def __init__(self, path="~/test.jpg"):
		self.path = path
		self.active = True
		self.last_photo = 0

	def work(self):
		# TODO activate lights inside the working area

		while self.active:
			now = time.time()
			if now - self.last_photo >= 2:
				self._makePhoto()
			else:
				time.sleep(2 - (now - self.last_photo))

		# TODO deactive light inside the working area

	def _makePhoto(self):
		call(["raspistill", "--timeout", "0", "--mode", "2", "-o", self.path])
		# call(["raspistill", "--timeout", "500", "--width", "1296", "--height", "972", "--quality", "70",
		#       "-o", self.path])
