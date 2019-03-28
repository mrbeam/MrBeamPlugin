import sys
import datetime
import logging
import collections
import copy
import threading
import traceback
from inspect import getframeinfo, stack


_printer = None


def init_mrb_logger(printer):
	global _printer
	_printer = printer

def mrb_logger(id):
	return MrbLogger(id)


class MrbLogger(object):

	LEVEL_COMM = '_COMM_'

	TERMINAL_BUFFER_DELAY = 2.0

	terminal_buffer = collections.deque(maxlen=100)

	def __init__(self, id, ignorePrinter=False):
		global _printer
		self.logger = logging.getLogger(id)
		self.id = id
		self.id_short = self._shorten_id(id)
		self.my_buffer = []
		# TODO: this line overrides logging.yaml!!!
		self.logger.setLevel(logging.DEBUG)

	def comm(self, msg, *args, **kwargs):
		kwargs['id'] = ''
		self._terminal(self.LEVEL_COMM, msg, *args, **kwargs)

	def debug(self, msg, *args, **kwargs):
		self.log(logging.DEBUG, msg, *args, **kwargs)

	def info(self, msg, *args, **kwargs):
		self.log(logging.INFO, msg, *args, **kwargs)

	def warn(self, msg, *args, **kwargs):
		self.log(logging.WARN, msg, *args, **kwargs)

	def warning(self, msg, *args, **kwargs):
		self.log(logging.WARN, msg, *args, **kwargs)

	def error(self, msg, *args, **kwargs):
		self.log(logging.ERROR, msg, *args, **kwargs)

	def critical(self, msg, *args, **kwargs):
		self.log(logging.CRITICAL, msg, *args, **kwargs)

	def exception(self, msg, *args, **kwargs):
		kwargs['analytics'] = True
		kwargs['exc_info'] = True
		self.log(logging.ERROR, msg, *args, **kwargs)

	def log(self, level, msg, *args, **kwargs):
		"""
		Logs the given message like the regular python logger. Still there are mrb-specific options available.
		:param level: log level
		:param msg: the message to log
		:param args: arguments to logger or to the message
		:param terminal: log this message also in Mr Beam frontend terminal
		:param terminal_as_comm: log this message also in Mr Beam frontend terminal as like it comes from COMM
		:param serial: log this message also in getLogger("SERIAL")
		:param analytics: Log this log event to analytics
		:param terminal_dump: Collect and log a terminal dump. Terminal dumps are also sent to analytics if analytics is not explicitly set to False.
		:type kwargs:
		"""
		if kwargs.pop('terminal', True if level >= logging.WARN else False):
			self._terminal(level, msg, *args, **kwargs)
		if kwargs.pop('terminal_as_comm', False):
			self._terminal(self.LEVEL_COMM, msg, *args, **kwargs)
		if kwargs.pop('serial', False):
			self._serial(msg, *args, **kwargs)
		analytics =  kwargs.pop('analytics', None)
		terminal_dump =  kwargs.pop('terminal_dump', False)
		if terminal_dump:
			analytics = True if analytics is not False else False
			self._dump_terminal_buffer(level=level, analytics=analytics)
		if analytics:
			kwargs['terminal_dump'] = terminal_dump
			self._analytics_log_event(level, msg, *args, **kwargs)
		# just to be shure....
		kwargs.pop('terminal', None)
		kwargs.pop('terminal_as_comm', None)
		kwargs.pop('analytics', None)
		kwargs.pop('terminal_dump', None)
		self.logger.log(level, msg, *args, **kwargs)

	def _terminal(self, level, msg, *args, **kwargs):
		global _printer

		date = self._getDateString()
		id = kwargs.pop('id', self.id_short)

		level = logging._levelNames[level] if level in logging._levelNames else level

		msg = msg % args if args and msg else msg
		exception = ''
		if kwargs.pop('exc_info', False):
			exctype, value = sys.exc_info()[:2]
			exception = " (Exception: {type} - {value})".format(type=(exctype.__name__ if exctype else None), value=value)
		output = "{date} {level}{space}{id}: {msg}{exception}".format(date=date, space=(' ' if id else ''), id=id, level=level, msg=msg, exception=exception)

		if level == self.LEVEL_COMM:
			MrbLogger.terminal_buffer.append(output)

		if _printer:
			_printer.on_comm_log(output)
		else:
			logging.getLogger("octoprint.plugins.mrbeam.terminal").warn("Can't log to terminal since _printer is None. Message: %s", msg)

	def _serial(self, msg, *args, **kwargs):
		msg = msg % args if args and msg else msg
		logging.getLogger("SERIAL").debug(msg)

	def _analytics_log_event(self, level, msg, *args, **kwargs):
		analytics_handler = self._get_analytics_handler()
		if analytics_handler is not None:
			try:
				msg = msg % args if args and msg else msg
				caller = None
				caller_myself = getframeinfo(stack()[0][0])
				i = 1
				while caller is None or caller.filename == caller_myself.filename:
					caller = getframeinfo(stack()[i][0])
					i += 1

				exception_str = None
				stacktrace = None
				if kwargs.get('exc_info', 0):
					exctype, value, tb = sys.exc_info()
					exception_str = "{}: '{}'".format(exctype.__name__ if exctype is not None else None, value)
					stacktrace = traceback.format_tb(tb)

				analytics_handler.log_event(
					level,
					msg,
					module = self.id,
					component = _mrbeam_plugin_implementation._identifier,
					component_version = _mrbeam_plugin_implementation._plugin_version,
					caller=caller,
					exception_str=exception_str,
					stacktrace=stacktrace,
					wait_for_terminal_dump=kwargs.get('terminal_dump', False))
			except:
				self.logger.exception("Exception in _analytics_log_event: ")


	def _dump_terminal_buffer(self, level=logging.INFO, repeat=True, analytics=True):
		try:
			if repeat:
				self.my_buffer = copy.copy(MrbLogger.terminal_buffer)
			else:
				self.my_buffer.extend(MrbLogger.terminal_buffer)
			MrbLogger.terminal_buffer.clear()

			if repeat:
				temp_timer = threading.Timer(self.TERMINAL_BUFFER_DELAY, self._dump_terminal_buffer, kwargs=(dict(level=level, repeat=False, analytics=analytics)))
				temp_timer.daemon = True
				temp_timer.name = "MrbLoggerTimer"
				temp_timer.start()
			else:
				tmp_arr = []
				my_logger = logging.getLogger('octoprint.plugins.mrbeam.terminal_dump')
				my_logger.log(level, " ******* Dumping terminal buffer (len: %s, analytics: %s)", len(self.my_buffer), analytics)
				for line in self.my_buffer:
					my_logger.log(level, line)
					tmp_arr.append(line)
				if analytics:
					analytics_handler = self._get_analytics_handler()
					if analytics_handler is not None:
						analytics_handler.log_terminal_dump(tmp_arr)
				self.my_buffer.clear()
		except:
			self.logger.exception("Exception in MrbLogger::dump_terminal_buffer() ")

	def _shorten_id(self, id):
		return id.replace('octoprint.plugins.', '')

	def _getDateString(self):
		return datetime.datetime.now().strftime("%H:%M:%S,%f")[:-3]
		# return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

	def _get_analytics_handler(self):
		analytics_handler = None
		try:
			analytics_handler = _mrbeam_plugin_implementation._analytics_handler
		except:
			self.logger.error("Not able to get analytics_handler.")
		return analytics_handler
