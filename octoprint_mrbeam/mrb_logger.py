import sys
import datetime
import logging


_printer = None

def init_mrb_logger(printer):
	global _printer
	_printer = printer


def mrb_logger(id):
	return MrbLogger(id)


class MrbLogger(object):

	def __init__(self, id, ignorePrinter=False):
		global _printer
		self.logger = logging.getLogger(id)
		self.id = self._shorten_id(id)


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

		if _printer:
			_printer.on_comm_log(output)
		else:
			logging.getLogger("octoprint.plugins.mrbeam.terminal").warn("Can't log to terminal since _printer is None. Message: %s", msg)


	def comm(self, msg, *args, **kwargs):
		self._terminal(msg, *args, level='_COMM_', id='', **kwargs)

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

	def _shorten_id(self, id):
		return id.replace('octoprint.plugins.', '')

	def _getDateString(self):
		return datetime.datetime.now().strftime("%H:%M:%S,%f")[:-3]
		# return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

