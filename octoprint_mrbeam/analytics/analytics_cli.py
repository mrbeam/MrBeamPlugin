#!/usr/bin/env python

import sys
import json
import datetime
from jobcontroller import JobController


if __name__ == "__main__":
	jsonfile = '/home/pi/.octoprint/analytics/analytics_log.json'

	if len(sys.argv) > 1:
		jsonfile = sys.argv[1]

	jobs = JobController()

	with open(jsonfile, 'r') as f:
		for line in f:
			try:
				data = json.loads(line.strip('\x00'))
			except ValueError as e:
				print "{}: {}".format(e.message, repr(line))
				continue

			if data['type'] == "deviceinfo":
				print "Analytics for device: {}\nSerialnumber: {}".format(data['hostname'], data['serialnumber'])
			elif data['type'] == "jobevent":
				jobs.addEvent(data)
		jobs.finishLastJob()

	print "Successful jobs: {}".format(jobs.getSuccessfulJobs())
	print "Cancelled jobs: {}".format(jobs.getCancelledJobs())
	print "Failed jobs: {}".format(jobs.getFailedJobs())
	print "Unknown jobs: {}".format(jobs.getUnknownJobs())
	print "Total job count: {}".format(jobs.getTotalJobs())

	runtime = datetime.timedelta(jobs.getTotalRunTime())
	pause = datetime.timedelta(jobs.getTotalPauseTime())
	cooling = datetime.timedelta(jobs.getTotalCoolingTime())

	print "Total job runtime: ".format(runtime)
	print "Total pause time: ".format(pause)
	print "pause time: ".format(pause-cooling)
	print "cooling time: ".format(cooling)
	print "Total laser runtime: ".format(runtime-pause)
