from job import Job, StartNewJob

class JobController(object):
	def __init__(self):
		self._joblist = list()
		self._currentjob = None

	def addEvent(self, event):
		if self._currentjob is None:
			self._currentjob = Job()

		try:
			self._currentjob.addEvent(event)
		except StartNewJob:
			self._joblist.append(self._currentjob)
			self._currentjob = Job()
			self._currentjob.addEvent(event)
		if self._currentjob.isFinished():
			self._joblist.append(self._currentjob)
			self._currentjob = None

	def finishLastJob(self):
		if self._currentjob is not None:
			if self._currentjob.finishJob():
				self._joblist.append(self._currentjob)
			self._currentjob = None

	def getTotalRunTime(self):
		totalruntime = 0
		for j in self._joblist:
			totalruntime += j.getRunTime()
		if self._currentjob is not None:
			totalruntime += self._currentjob.getRunTime()
		return totalruntime

	def getTotalPauseTime(self):
		totalpausetime = 0
		for j in self._joblist:
			totalpausetime += j.getTotalPauseTime()
		return totalpausetime

	def getTotalJobs(self):
		if self._currentjob is None:
			return len(self._joblist)
		else:
			return len(self._joblist)+1

	def getSuccessfulJobs(self):
		successfulsum = 0
		for j in self._joblist:
			if j.getstate() == Job.JOB_STATE_SUCCESSFUL:
				successfulsum += 1
		return successfulsum

	def getCancelledJobs(self):
		cancelledsum = 0
		for j in self._joblist:
			if j.getstate() == Job.JOB_STATE_CANCELLED:
				cancelledsum += 1
		return cancelledsum

	def getFailedJobs(self):
		failedsum = 0
		for j in self._joblist:
			if j.getstate() == Job.JOB_STATE_FAILED:
				failedsum += 1
		return failedsum

	def getUnknownJobs(self):
		unknownsum = 0
		for j in self._joblist:
			if j.getstate() == Job.JOB_STATE_UNKNOWN:
				unknownsum += 1
		return unknownsum
