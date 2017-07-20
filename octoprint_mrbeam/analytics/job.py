class Job(object):

	JOB_STATE_RUNNING    = "Running"
	JOB_STATE_PAUSED     = "Paused"
	JOB_STATE_RESUMED    = "Resumed"
	JOB_STATE_SUCCESSFUL = "Successful"
	JOB_STATE_CANCELLED  = "Cancelled"
	JOB_STATE_FAILED     = "Failed"
	JOB_STATE_UNKNOWN    = "Unknown"

	def __init__(self):
		self._starttime = None
		self._endtime = None
		self._lastprogresstime = None
		self._lastprogressvalue = None
		self._pauselist = list()
		self._currentpause = None
		self._state = None

	def addEvent(self, event):
		if event['eventname'] == "print_started":
			self._addStartEvent(event)
		elif self._starttime is not None:
			if event['eventname'] == "print_progress":
				self._addPrintProgress(event)
			elif event['eventname'] == "print_done":
				self._addDoneEvent(event)
			elif event['eventname'] == "print_cancelled":
				self._addCancelEvent(event)
			elif event['eventname'] == "print_failed":
				self._addFailedEvent(event)
			elif event['eventname'] == "print_paused":
				self._addPrintPaused(event)
			elif event['eventname'] == "print_resumed":
				self._addPrintResumed(event)
			elif event['eventname'] == "laser_cooling_pause":
				self._addCoolingPause(event)
			elif event['eventname'] == "laser_cooling_resume":
				self._addCoolingResume(event)

	def finishJob(self):
		if self._starttime is None:
			return False
		else:
			if self._lastprogresstime is not None:
				self._endtime = self._lastprogresstime
			else:
				self._endtime = self._starttime
			self._state = self.JOB_STATE_UNKNOWN
			return True

	def isFinished(self):
		if self._state in (self.JOB_STATE_SUCCESSFUL, self.JOB_STATE_CANCELLED, self.JOB_STATE_FAILED, self.JOB_STATE_UNKNOWN):
			return True
		else:
			return False

	def getstate(self):
		return self._state

	def getRunTime(self):
		return self._endtime - self._starttime

	def getTotalPauseTime(self):
		totalsum = 0
		for p in self._pauselist:
			totalsum += p.getPauseTime()
		return totalsum

	def getTotalCoolingTime(self):
		totalsum = 0
		for p in self._pauselist:
			totalsum += p.getCoolingTime()
		return totalsum

	def _addStartEvent(self, event):
		if self._starttime is None:
			self._starttime = event['timestamp']
			self._state = self.JOB_STATE_RUNNING
		else:
			if self._lastprogresstime is not None:
				self._endtime = self._lastprogresstime
			else:
				self._endtime = self._starttime
			self._state = self.JOB_STATE_UNKNOWN
			raise StartNewJob("Starttime allready set, please start new job with the same event.")

	def _addDoneEvent(self, event):
		if self._endtime is None:
			self._endtime = event['timestamp']
			self._state = self.JOB_STATE_SUCCESSFUL

	def _addCancelEvent(self, event):
		if self._endtime is None:
			self._endtime = event['timestamp']
			self._state = self.JOB_STATE_CANCELLED

	def _addFailedEvent(self, event):
		if self._endtime is None:
			self._endtime = event['timestamp']
			self._state = self.JOB_STATE_FAILED

	def _addPrintPaused(self, event):
		if self._currentpause is None:
			self._currentpause = Pause(event['timestamp'])
			self._state = self.JOB_STATE_PAUSED

	def _addPrintResumed(self, event):
		if self._currentpause is not None:
			self._currentpause.addEndtime(event['timestamp'])
			self._pauselist.append(self._currentpause)
			self._currentpause = None
			self._state = self.JOB_STATE_RESUMED

	def _addCoolingPause(self, event):
		if self._currentpause is not None:
			self._currentpause.addStartCooling(event['timestamp'])

	def _addCoolingResume(self, event):
		if self._currentpause is not None:
			self._currentpause.addEndCooling(event['timestamp'])

	def _addPrintProgress(self, event):
		self._lastprogresstime = event['timestamp']
		self._lastprogressvalue = event['progress']

class Pause(object):
	def __init__(self, starttime):
		self._starttime = None
		self._endtime = None
		self._startCooling = None
		self._endCooling = None
		self.addStarttime(starttime)

	def addStarttime(self, time):
		self._starttime = time

	def addEndtime(self, time):
		self._endtime = time

	def addStartCooling(self, time):
		self._startCooling = time

	def addEndCooling(self, time):
		if self._startCooling is not None:
			self._endCooling = time

	def getPauseTime(self):
		return self._endtime - self._starttime

	def getCoolingTime(self):
		if self._startCooling is None:
			return 0
		else:
			if self._endCooling is None:
				return self._endtime - self._startCooling
			else:
				return self._endCooling - self._startCooling

	def getPauseStarttime(self):
		return self._starttime

	def getPauseEndtime(self):
		return self._endtime

class StartNewJob(Exception):
	pass
