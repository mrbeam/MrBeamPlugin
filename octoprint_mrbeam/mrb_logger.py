import sys
import datetime
import logging
import collections
import copy
import threading
import traceback
from inspect import getframeinfo, stack
from logging import getLogger, Logger
from octoprint_mrbeam.util import force_kwargs


_printer = None
LEVEL_COMM = '_COMM_'
TERMINAL_BUFFER_DELAY = 2.0
DEFAULT_KWARGS = dict(
	analytics=False,
	terminal=None,
	terminal_dump=False,
	terminal_as_comm=False,
	serial=False,
)
DEFAULT_COMM = dict(id=None, exc_info=False)

def init_mrb_logger(printer):
	global _printer
	_printer = printer

def mrb_logger(name, lvl=None):
	logger = getLogger(name)
	if lvl is not None:
		logger.setLevel(lvl)
	return logger


class MrbLogger(Logger):

	terminal_buffer = collections.deque(maxlen=100)

	def __init__(self, name, ignorePrinter=False, level=logging.INFO):
		Logger.__init__(self, name, level)
		global _printer
		self.name_short = name.replace('octoprint.plugins.', '').replace('octoprint_mrbeam', 'mrbeam')
		self.my_buffer = []

	@force_kwargs(**DEFAULT_COMM)
	def comm(self, msg, id=None, *args, **kwargs):
		if self.isEnabledFor(LEVEL_COMM):
			self._terminal(LEVEL_COMM, msg, id=id, *args, **kwargs)

	@force_kwargs(**DEFAULT_KWARGS)
	def debug(self, msg, *args, **kwargs):
		if self.isEnabledFor(logging.DEBUG):
			self._log(logging.DEBUG, msg, args, **kwargs)

	@force_kwargs(**DEFAULT_KWARGS)
	def info(self, msg, *args, **kwargs):
		if self.isEnabledFor(logging.INFO):
			self._log(logging.INFO, msg, args, **kwargs)

	@force_kwargs(**DEFAULT_KWARGS)
	def warning(self, msg, *args, **kwargs):
		if self.isEnabledFor(logging.WARNING):
			self._log(logging.WARNING, msg, args, **kwargs)

	warn = warning

	# Activate analytics by default for log levels > ERROR
	@force_kwargs(**DEFAULT_KWARGS)
	def error(self, msg, analytics=True, *args, **kwargs):
		if self.isEnabledFor(logging.ERROR):
			self._log(logging.ERROR, msg, args, analytics=analytics, **kwargs)

	@force_kwargs(**DEFAULT_KWARGS)
	def critical(self, msg, analytics=True, *args, **kwargs):
		if self.isEnabledFor(logging.CRITICAL):
			self._log(logging.CRITICAL, msg, args, analytics=analytics, **kwargs)

	# Disable the exception stacktrace AXEL : but why?
	@force_kwargs(**DEFAULT_KWARGS)
	def exception(self, msg, analytics=True, exc_info=False, *args, **kwargs):
		# kwargs[''] = kwargs.get('exc_info', True) # why?
		if self.isEnabledFor(logging.ERROR):
			self._log(logging.ERROR, msg, args, analytics=analytics, exc_info=exc_info, **kwargs)

	# @force_kwargs(**DEFAULT_KWARGS)
	def _log(
		self,
		level,
		msg,
		args,
		analytics=False,
		terminal=None,
		terminal_dump=False,
		terminal_as_comm=False,
		serial=False,
		**kwargs
	):
		"""
		Logs the given message like the regular python logger. Still there are mrb-specific options available.
		:param level: log level
		:param msg: the message to log
		:param args: arguments to logger or to the message
		:param terminal: log this message also in Mr Beam frontend terminal
		:param terminal_as_comm: log this message also in Mr Beam frontend terminal as like it comes from COMM
		:param serial: log this message also in getLogger("SERIAL")
		:param analytics: Log this log event to analytics
		:type  analytics: Union[basestring, bool]
		:param terminal_dump: Collect and log a terminal dump. Terminal dumps are also sent to analytics if analytics is not explicitly set to False.
		:type kwargs:
		"""
		if terminal or (terminal is None and level >= logging.WARN):
			self._terminal(level, msg, *args, **kwargs)
		if terminal_as_comm or level == LEVEL_COMM:
			kwargs['id'] = ''
			self._terminal(LEVEL_COMM, msg, *args, **kwargs)
			del kwargs['id']
		if serial:
			self._serial(msg, *args, **kwargs)
		if terminal_dump:
			self._dump_terminal_buffer(level=level, analytics=analytics)
		if analytics:
			# Analytics can be a boolean or a string. If it's a string, we use it as the analytics_id
			if isinstance(analytics, basestring):
				analytics_id = analytics
			else:
				analytics_id = None

			self._analytics_log_event(level, msg, analytics_id, terminal_dump=terminal_dump, *args, **kwargs)
		Logger._log(self, level, msg, args, **kwargs) # The parent log

	@force_kwargs(**DEFAULT_COMM)
	def _terminal(self, level, msg, id=None, exc_info=False, *args, **kwargs):
		global _printer

		date = MrbLogger._getDateString()
		id = id or self.name_short # FIXME id is reserved

		level = logging._levelNames[level] if level in logging._levelNames else level

		msg = msg % args if args and msg else msg
		exception = ''
		if exc_info:
			exctype, value, _ = sys.exc_info()
			exception = " (Exception: {type} - {value})".format(type=(exctype.__name__ if exctype else None), value=value)
		output = "{date} {level}{space}{id}: {msg}{exception}".format(date=date, space=(' ' if id else ''), id=id, level=level, msg=msg, exception=exception)

		if level == LEVEL_COMM:
			MrbLogger.terminal_buffer.append(output)

		if _printer:
			_printer.on_comm_log(output)
		else:
			logging.getLogger(__name__, msg)

	def _serial(self, msg, *args, **kwargs):
		logging.getLogger("SERIAL").debug(msg, *args, **kwargs)

	def _analytics_log_event(self, level, msg, analytics_id, exc_info=0, terminal_dump=False, *args, **kwargs):
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
				if exc_info:
					exctype, value, tb = sys.exc_info()
					exctype_name = exctype.__name__ if exctype is not None else None
					exception_str = "{}: '{}'".format(exctype_name, value)
					stacktrace = traceback.format_tb(tb)
					msg = "{} - Exception: {}".format(msg, exception_str)

				event_details = dict(
					level=level,
					analytics_id=analytics_id,
					msg=msg,
					module=self.name,
					component=_mrbeam_plugin_implementation._identifier,
					component_version=_mrbeam_plugin_implementation.get_plugin_version(),
					caller=caller,
					exception_str=exception_str,
					stacktrace=stacktrace,
				)

				analytics_handler.add_logger_event(
					event_details, wait_for_terminal_dump=terminal_dump)

			except:
				self.exception("Exception in _analytics_log_event: ", analytics=False)
		else:
			self.error('Could not write exception to analytics, the analytics handler was not initialized.', analytics=False)

	def _dump_terminal_buffer(self, level=logging.INFO, repeat=True, analytics=True):
		try:
			if repeat:
				self.my_buffer = copy.copy(MrbLogger.terminal_buffer)
			else:
				self.my_buffer.extend(MrbLogger.terminal_buffer)
			MrbLogger.terminal_buffer.clear()

			if repeat:
				temp_timer = threading.Timer(TERMINAL_BUFFER_DELAY, self._dump_terminal_buffer, kwargs=(dict(level=level, repeat=False, analytics=analytics)))
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
			self.exception("Exception in MrbLogger::dump_terminal_buffer() ", analytics=analytics)

	@classmethod
	def _getDateString(cls):
		return datetime.datetime.now().strftime("%H:%M:%S,%f")[:-3]
		# return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

	def _get_analytics_handler(self):
		try:
			return _mrbeam_plugin_implementation.analytics_handler
		except:
			self.error("Not able to get analytics_handler.", analytics=False)
			return
