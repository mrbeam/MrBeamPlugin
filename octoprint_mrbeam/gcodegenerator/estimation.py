"""
This script takes a gcode file as an input and calculates an estimated job duration time.

It reads the gcode line by line extracting the coordinates and feed rates, and with those values calculates the duration
of each of the ways. Finally it sums up all the durations to get the total duration.
The
"""

import re
from math import hypot
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
import threading

FIND_X_VALUE = r"X(\d+\.?\d+)"
FIND_Y_VALUE = r"Y(\d+\.?\d+)"
FIND_FEEDRATE = r"F(\d+\.?\d+)"


class Estimation:
	def __init__(self, event_bus):
		self._event_bus = event_bus
		self._logger = mrb_logger("octoprint.plugins.mrbeam.estimation")

		self._subscribe()

	# EVENTS
	def _subscribe(self):
		"""Subscribe to OctoPrint's SLICING_DONE event.

		Returns:
			None
		"""

		self._event_bus.subscribe(OctoPrintEvents.SLICING_DONE, self.on_event)

	def on_event(self, event, payload):
		"""Start estimation calculation in a new thread when SLICING_DONE.

		Args:
			event(OctoprintEvent): the name of the event that triggers the function.
			payload(dict): the payload of the event that triggers the function.

		Returns:
			None
		"""

		if event == OctoPrintEvents.SLICING_DONE:
			estimation_thread = threading.Thread(target=self._calculate_estimation_threaded,
												 name="estimation._calculate_estimation_threaded",
												 args=(payload['gcode'],))
			estimation_thread.daemon = True
			estimation_thread.start()

	def _calculate_estimation_threaded(self, file_name):
		"""Calculate the job time estimation from the gcode file.

		Args:
			file_name(str): the name of the gcode file.

		Returns:
			None
		"""

		try:
			self._logger.debug("Starting thread for job time estimation")
			path = _mrbeam_plugin_implementation._settings.getBaseFolder("uploads")
			gcode_file = '{path}/{file}'.format(file=file_name, path=path)

			payload = dict()
			payload['estimation'] = self.estimate_job_duration(gcode_file)
			_mrbeam_plugin_implementation.fire_event(MrBeamEvents.JOB_TIME_ESTIMATED, payload)
		except:
			self._logger.exception("Error when calculating the job duration estimation")

	# ESTIMATION
	@staticmethod
	def distance(x1, y1, x2, y2):
		"""Calculate the distance between two coordinates (the hypotenuse).

		Args:
			x1(float): the x value of the first coordinate.
			y1(float): the y value of the first coordinate.
			x2(float): the x value of the second coordinate.
			y2(float): the y value of the second coordinate.

		Returns:
			The distance between the coordinates.
		"""

		return hypot(x2 - x1, y2 - y1)

	@staticmethod
	def longest_axis_distance(x1, y1, x2, y2):
		"""Calculate the distance of the longest axis between two coordinates.

		Args:
			x1(float): the x value of the first coordinate.
			y1(float): the y value of the first coordinate.
			x2(float): the x value of the second coordinate.
			y2(float): the y value of the second coordinate.

		Returns:
			The distance of the axis with the longest distance.
		"""

		if abs(x1 - x2) > abs(y1 - y2):
			return abs(x1 - x2)
		else:
			return abs(y1 - y2)

	@staticmethod
	def seconds_to_time_string(seconds):
		"""Format the seconds as a time string.

		Args:
			seconds(int): the seconds to represent.

		Returns:
			time_string(str): a string with the representation of the time.
		"""

		seconds = int(seconds)
		hours, reminder = divmod(seconds, 3600)
		minutes, seconds = divmod(reminder, 60)

		time_string = "TOTAL DURATION: {hh:02d}:{mm:02d}:{ss:02d}".format(hh=hours, mm=minutes, ss=seconds)
		return time_string

	@staticmethod
	def _round_duration_to(total_duration, round_to, to_minutes=True):
		"""Round the duration to a determined time.

		Args:
			total_duration(float): the estimated total duration in seconds.
			round_to(int): the value to which the duration has to be rounded.
			to_minutes(bool): indicates if the value to be rounded to is in minutes (default) or seconds.

		Returns:
			total_duration(int): the rounded up duration in seconds.
		"""

		if to_minutes:
			seconds = 60
		else:
			seconds = 1

		quotient, reminder = divmod(total_duration, round_to * seconds)
		if reminder > round_to / 2:
			total_duration = total_duration - reminder + round_to * seconds
		else:
			total_duration = total_duration - reminder
		return total_duration

	def round_total_duration(self, total_duration):
		"""Round the total duration depending on its value.

		Args:
			total_duration(float): the estimated total duration in seconds.

		Returns:
			total_duration(int): the estimated total duration after being rounded up.
		"""

		# Increase by 10%
		total_duration = total_duration * 1.1

		# x > 4h --> round to 30 minutes
		if total_duration > 4 * 3600:
			total_duration = self._round_duration_to(total_duration, 30, True)

		# 4h > x > 2h --> round to 15 minutes
		elif total_duration > 2 * 3600:
			total_duration = self._round_duration_to(total_duration, 15, True)

		# 2h > x > 1h --> round to 10 minutes
		elif total_duration > 1 * 3600:
			total_duration = self._round_duration_to(total_duration, 10, True)

		# 1h > x > 30min --> round to 5 minutes
		elif total_duration > 30 * 60:
			total_duration = self._round_duration_to(total_duration, 5, True)

		elif total_duration > 1 * 60:
			total_duration = self._round_duration_to(total_duration, 1, True)

		# x < 1min --> Just say 1 minute
		else:
			total_duration = 60

		return total_duration

	def estimate_job_duration(self, gcode_file):
		"""Read a gcode file and calculate what will be the total duration of the job.
		Reads the G0 and G1 commands to extract the coordinates and the F commands to get the feed rates.

		Args:
			gcode_file(str): the path to the gcode file.

		Returns:
			total_duration(float): the calculated total duration of the job.
		"""

		with open(gcode_file, 'r') as gfile:
			content = gfile.readlines()
			x = 500
			y = 390
			feedrate = 0
			max_feedrate = 5000

			total_duration = 0

			for line in content:
				first_char = line[0]
				if first_char == 'G':
					command = line[1:]
					second_char = command[0]

					# Save previous values
					old_x = x
					old_y = y
					old_f = feedrate

					# Extract x and y coordinates
					try:
						x = float(re.findall(FIND_X_VALUE, command)[0])
					except IndexError:
						x = old_x

					try:
						y = float(re.findall(FIND_Y_VALUE, command)[0])
					except IndexError:
						y = old_y

					# Rapid: Travel at maximum speed to the coordinates (not for lasering)
					if second_char == '0':
						duration = self.longest_axis_distance(x, y, old_x, old_y) / max_feedrate * 60
						total_duration += duration

					# Move with a specific rate
					elif second_char == '1':
						try:
							feedrate = float(re.findall(FIND_FEEDRATE, command)[0])
						except IndexError:
							feedrate = old_f

						duration = self.distance(x, y, old_x, old_y) / feedrate * 60
						total_duration += duration

				elif first_char == 'F':
					feedrate = float(re.findall(FIND_FEEDRATE, line)[0])

		total_duration_rounded = self.round_total_duration(total_duration)

		return total_duration_rounded
