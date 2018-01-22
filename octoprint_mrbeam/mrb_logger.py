import sys
import datetime
import logging
import collections
import copy
import threading


_printer = None


def init_mrb_logger(printer):
	global _printer
	_printer = printer

def mrb_logger(id):
	return MrbLogger(id)


class MrbLogger(object):

	LEVEL_COMM = '_COMM_'

	terminal_buffer = collections.deque(maxlen=100)

	def __init__(self, id, ignorePrinter=False):
		global _printer
		self.logger = logging.getLogger(id)
		self.id = self._shorten_id(id)
		self.my_buffer = []
		# TODO: this line overrides logging.yaml!!!
		self.logger.setLevel(logging.DEBUG)


	def _terminal(self, msg, *args, **kwargs):
		global _printer

		date = self._getDateString()
		id = kwargs.pop('id', self.id)
		level = kwargs.pop('level', '')
		msg = msg % args if args and msg else msg
		exception = ''
		if kwargs.pop('exc_info', False):
			exctype, value = sys.exc_info()[:2]
			exception = " (Exception: {type} - {value})".format(type=exctype, value=value)
		output = "{date} {level}{space}{id}: {msg}{exception}".format(date=date, space=(' ' if id else ''), id=id, level=level, msg=msg, exception=exception)

		if level == self.LEVEL_COMM:
			MrbLogger.terminal_buffer.append(output)

		if _printer:
			_printer.on_comm_log(output)
		else:
			logging.getLogger("octoprint.plugins.mrbeam.terminal").warn("Can't log to terminal since _printer is None. Message: %s", msg)


	def comm(self, msg, *args, **kwargs):
		self._terminal(msg, *args, level=self.LEVEL_COMM, id='', **kwargs)

	def debug(self, msg, *args, **kwargs):
		if kwargs.pop('terminal', False):
			self._terminal(msg, *args, level='DEBUG', **kwargs)
		self.logger.debug(msg, *args, **kwargs)

	def info(self, msg, *args, **kwargs):
		if kwargs.pop('terminal', False):
			self._terminal(msg, *args, level='INFO', **kwargs)
		self.logger.info(msg, *args, **kwargs)

	def warn(self, msg, *args, **kwargs):
		self.warning(msg, *args, **kwargs)

	def warning(self, msg, *args, **kwargs):
		if kwargs.pop('terminal', True):
			self._terminal(msg, *args, level='WARNING', **kwargs)
		self.logger.warn(msg, *args, **kwargs)

	def error(self, msg, *args, **kwargs):
		if kwargs.pop('terminal', True):
			self._terminal(msg, *args, level='ERROR', **kwargs)
		self.logger.error(msg, *args, **kwargs)

	def critical(self, msg, *args, **kwargs):
		if kwargs.pop('terminal', True):
			self._terminal(msg, *args, level='CRITICAL', **kwargs)
		self.logger.critical(msg, *args, **kwargs)

	def exception(self, msg, *args, **kwargs):
		if kwargs.pop('terminal', True):
			self._terminal(msg, *args, level='EXCEPTION', exc_info=True, **kwargs)
		self.logger.exception(msg, *args, **kwargs)

	def dump_terminal_buffer(self, level=logging.INFO, repeat=True):
		if repeat:
			self.my_buffer = copy.copy(MrbLogger.terminal_buffer)
		else:
			self.my_buffer.extend(MrbLogger.terminal_buffer)
		MrbLogger.terminal_buffer.clear()

		if repeat:
			temp_timer = threading.Timer(2.0, self.dump_terminal_buffer, kwargs=(dict(level=level, repeat=False)))
			temp_timer.daemon = True
			temp_timer.name = "MrbLoggerTimer"
			temp_timer.start()
		else:
			my_logger = logging.getLogger('octoprint.plugins.mrbeam.terminal_dump')
			my_logger.log(level, " ******* Dumping terminal buffer (len: %s)", len(self.my_buffer))
			for line in self.my_buffer:
				my_logger.log(level, line)
			self.my_buffer.clear()

	def _shorten_id(self, id):
		return id.replace('octoprint.plugins.', '')

	def _getDateString(self):
		return datetime.datetime.now().strftime("%H:%M:%S,%f")[:-3]
		# return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

