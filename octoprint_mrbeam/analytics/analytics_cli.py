#!/usr/bin/env python

import sys
import json
from jobcontroller import JobController


if __name__ == "__main__":
	jsonfile = '/home/pi/.octoprint/analytics_log.json'

	if len(sys.argv) > 1:
		jsonfile = sys.argv[1]

	jobs = JobController()

	with open(jsonfile, 'r') as f:
		for line in f:
			data = json.loads(line)

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
	print "Total job runtime: {0:.2f} [min]".format(jobs.getTotalRunTime() / 60.0)
	print "Total laser runtime: {0:.2f} [min]".format((jobs.getTotalRunTime() - jobs.getTotalPauseTime()) / 60.0)
