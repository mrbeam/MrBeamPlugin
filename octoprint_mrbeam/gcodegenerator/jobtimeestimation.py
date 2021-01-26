"""
This script takes a gcode file as an input and calculates an estimated job duration time.

It reads the gcode line by line extracting the coordinates and feed rates, and with those values calculates the duration
of each of the ways. Finally it sums up all the durations to get the total duration.
The
"""

import re
import time
from math import hypot
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
import threading

FIND_X_VALUE = r"X(\d+\.?\d+)"
FIND_Y_VALUE = r"Y(\d+\.?\d+)"
FIND_FEEDRATE = r"F(\d+\.?\d+)"
MATCH_COMMENT_ADD_TIME = re.compile(r"EXTRA_TIME [\+-]?[0-9]+\.?[0-9]*s")


def time_from_comment(comment):
    """
    Returns the number of seconds read in the comment if the comment matches a float:
        ; [\+-]?[0-9]+\.?[0-9]*s

    Examples:
        >>> time_from_comment("EXTRA_TIME 0.19s")
        0.19
        >>> time_from_comment(";EXTRA_TIME +0.19s")
        0.19
        >>> time_from_comment(";EXTRA_TIME +50s")
        50.0
        >>> time_from_comment("; this is not a number")
        0.0
        >>> time_from_comment("; here is a number EXTRA_TIME -70s")
        -70.0
        >>> time_from_comment("; EXTRA_TIME not formatted 70")
        0.0
        >>> time_from_comment("cannot do 2 numbers EXTRA_TIME 6.9s EXTRA_TIME 42.0s")
        6.9
    """
    match = MATCH_COMMENT_ADD_TIME.search(comment)
    if match:
        float(match.group(1))
    else:
        return 0.0


class JobTimeEstimation:
    def __init__(self, plugin):
        self._plugin = plugin
        self._event_bus = plugin._event_bus
        self._settings = plugin._settings
        self._logger = mrb_logger("octoprint.plugins.mrbeam.job_time_estimation")

        self._last_estimation = -1
        self._meta = dict()

        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

    def _on_mrbeam_plugin_initialized(self, event, payload):
        self._subscribe()

    # EVENTS
    def _subscribe(self):
        """Subscribe to OctoPrint's SLICING_DONE event.

        Returns:
                None
        """

        self._event_bus.subscribe(OctoPrintEvents.SLICING_DONE, self.on_event)
        self._event_bus.subscribe(OctoPrintEvents.CLIENT_OPENED, self.on_event)

    def on_event(self, event, payload):
        """Start estimation calculation in a new thread when SLICING_DONE.

        Args:
                event(OctoprintEvent): the name of the event that triggers the function.
                payload(dict): the payload of the event that triggers the function.

        Returns:
                None
        """

        if event == OctoPrintEvents.SLICING_DONE:
            estimation_thread = threading.Thread(
                target=self._calculate_estimation_threaded,
                name="job_time_estimation._calculate_estimation_threaded",
                args=(payload["gcode"],),
            )
            estimation_thread.daemon = True
            estimation_thread.start()

        if event == OctoPrintEvents.CLIENT_OPENED and self._last_estimation != -1:
            self._send_estimate_to_frontend()

    def _calculate_estimation_threaded(self, file_name):
        """Calculate the job time estimation from the gcode file.

        Args:
                file_name(str): the name of the gcode file.

        Returns:
                None
        """

        try:
            self._logger.debug("Starting thread for job time estimation")
            path = self._settings.getBaseFolder("uploads")
            gcode_file = "{path}/{file}".format(file=file_name, path=path)

            self._last_estimation, self._meta = self.estimate_job_duration(gcode_file)
            self._send_estimate_to_frontend()
        except:
            self._logger.exception("Error when calculating the job duration estimation")

    def _send_estimate_to_frontend(self):
        try:
            payload = dict()
            payload["job_time_estimation"] = self._last_estimation
            payload["calc_duration_total"] = self._meta.get("calc_duration_total", -1)
            payload["calc_duration_woke"] = self._meta.get("calc_duration_woke", -1)
            payload["calc_lines"] = self._meta.get("calc_lines", -1)
            self._plugin.fire_event(MrBeamEvents.JOB_TIME_ESTIMATED, payload)
        except:
            self._logger.exception("Error when sending JobTimeEstimated event.")

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

        time_string = "TOTAL DURATION: {hh:02d}:{mm:02d}:{ss:02d}".format(
            hh=hours, mm=minutes, ss=seconds
        )
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

    def estimate_job_duration(self, gcode_file, do_sleep=True):
        """Read a gcode file and calculate what will be the total duration of the job.
        Reads the G0 and G1 commands to extract the coordinates and the F commands to get the feed rates.

        Args:
                gcode_file(str): the path to the gcode file.

        Returns:
                total_duration(float): the calculated total duration of the job.
        """

        with open(gcode_file, "r") as gfile:
            content = gfile.readlines()
            x = 500
            y = 390
            feedrate = 0
            max_feedrate = 5000

            total_duration = 0
            calc_lines = 0
            start_all_ts = time.time()
            start_wake_ts = time.time()
            calc_duration_woke = 0

            for line in content:
                calc_lines += 1
                first_char = line[0]
                if first_char == "G":
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
                    if second_char == "0":
                        duration = (
                            self.longest_axis_distance(x, y, old_x, old_y)
                            / max_feedrate
                            * 60
                        )
                        total_duration += duration

                    # Move with a specific rate
                    elif second_char == "1":
                        try:
                            feedrate = float(re.findall(FIND_FEEDRATE, command)[0])
                        except IndexError:
                            feedrate = old_f

                        duration = self.distance(x, y, old_x, old_y) / feedrate * 60
                        total_duration += duration

                    # prevent JTE from pulling to hard on the CPU if the
                    # user already started the job
                    if do_sleep and calc_lines % 100 == 0:
                        calc_duration_woke += time.time() - start_wake_ts
                        sleep_time = 0.002
                        # if self._plugin._printer.is_printing():
                        # 	sleep_time = 0.004
                        time.sleep(sleep_time)
                        start_wake_ts = time.time()

                elif first_char == "F":
                    feedrate = float(re.findall(FIND_FEEDRATE, line)[0])
                elif first_char == ";":
                    total_duration += time_from_comment(line)

        total_duration_rounded = self.round_total_duration(total_duration)
        calc_duration_woke += time.time() - start_wake_ts
        calc_duration_total = time.time() - start_all_ts

        return (
            total_duration_rounded,
            dict(
                calc_duration_woke=calc_duration_woke,
                calc_duration_total=calc_duration_total,
                calc_lines=calc_lines,
            ),
        )
