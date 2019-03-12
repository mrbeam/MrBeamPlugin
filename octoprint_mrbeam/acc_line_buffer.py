# coding=utf-8

import collections
from octoprint_mrbeam.lib.rwlock import RWLock

class AccLineBuffer(object):

	DEFAULT_HISTORY_LENGTH = 3

	def __init__(self):
		self._lock = RWLock()
		self.buffer_cmds = collections.deque()
		self.declined_cmds = collections.deque()
		self._last_responded = None
		self.char_len = -1
		self.id = 0

	def reset(self):
		self._lock.writer_acquire()
		self.buffer_cmds.clear()
		self.declined_cmds.clear()
		self._last_responded = None
		self._reset_char_len()
		self.id = 0
		self._lock.writer_release()

	def add(self, cmd, intensity, feedrate, pos_x, pos_y, laser):
		"""
		Add a new command (item)
		:param cmd:
		:param intensity: (optional) intensity BEFORE this command is executed
		:param feedrate: (optional) feedrate BEFORE this command is executed
		:param pos_x:
		:param pos_y:
		:param laser:
		"""
		self._lock.writer_acquire()
		d = dict(
			cmd=cmd,
			i=intensity,
			f=feedrate,
			x=pos_x,
			y=pos_y,
			l=laser,
			id=self.id
		)
		self.id += 1
		self.buffer_cmds.append(d)
		self._reset_char_len()
		self._lock.writer_release()

	def acknowledge_cmd(self):
		"""
		Remove the oldest command (item) from buffer
		Will be still available per get_last_acknowledged() iuntil this method is called next time
		and is ignored in get_command_count() and is_empty() and get_char_len()
		"""
		if self.is_empty():
			raise ValueError("AccLineBuffer is empty, no item to acknowledge.")
		self._lock.writer_acquire()
		self._last_responded = self.buffer_cmds.popleft()
		self._reset_char_len()
		self._lock.writer_release()
		return self._last_responded

	def decline_cmd(self):
		"""
		Removes the oldest command (item) from the buffer and keeps it as recovery command
		:return:
		:rtype:
		"""
		if self.is_empty():
			raise ValueError("AccLineBuffer is empty, no item to decline.")
		self._lock.writer_acquire()
		self._last_responded = self.buffer_cmds.popleft()
		self._reset_char_len()
		self.declined_cmds.append(self._last_responded)
		self._lock.writer_release()
		return self._last_responded

	def get_first_item(self):
		"""
		Returns the first (oldest) item. This is the one to be removed next.
		:return: item dict(cmd="", i=1, f=23) or None if empty
		"""
		if self.is_empty():
			return None
		self._lock.reader_acquire()
		res =  self.buffer_cmds[0]
		self._lock.reader_release()
		return res

	def get_last_responded(self):
		"""
		returns the last acknowledged command
		:return: item
		"""
		self._lock.reader_acquire()
		res = self._last_responded
		self._lock.reader_release()
		return res

	def recover_declined_commands(self):
		res = []
		self._lock.writer_acquire()
		for d in self.declined_cmds:
			res.append(d['cmd'].rstrip())
		self.declined_cmds.clear()
		self._lock.writer_release()
		return res

	# def get_last_declined(self):
	# 	"""
	# 	returns the last declined command without removing it
	# 	:return: item
	# 	"""
	# 	if len(self.declined_cmds) > 0:
	# 		return self.declined_cmds[0]
	# 	else:
	# 		return None

	# def remove_last_declined(self):
	# 	"""
	# 	removes the last declined command
	# 	:return: item
	# 	"""
	# 	if len(self.declined_cmds) > 0:
	# 		return self.declined_cmds.popleft()
	# 	else:
	# 		return None


	# def declined_num(self):
	# 	return len(self.declined_cmds)

	# def get_cmd_list(self):
	# 	res = []
	# 	self._lock.reader_acquire()
	# 	for c in self.buffer_cmds:
	# 		res.append(c['cmd'].rstrip())
	# 	self._lock.reader_release()
	# 	return res

	# def get_last_confirmed_item(self):
	# def get_last_item(self):
	# 	if self.is_empty():
	# 		return None
	# 	res = None
	# 	self._lock.reader_acquire()
	# 	if len(self.history) > 0:
	# 		res = self.history[len(self.history)-1]
	# 	self._lock.reader_release()
	# 	return res

	def get_command_count(self):
		"""
		Number of commands in buffer (ignores history)
		:return: int length
		"""
		self._lock.reader_acquire()
		res = len(self.buffer_cmds)
		self._lock.reader_release()
		return res

	def is_empty(self):
		"""
		True if the buffer is empty
		:return: boolean
		"""
		self._lock.reader_acquire()
		res = len(self.buffer_cmds) == 0
		self._lock.reader_release()
		return res

	def is_recovery_empty(self):
		"""
		True if the buffer is empty
		:return: boolean
		"""
		self._lock.reader_acquire()
		res = len(self.declined_cmds) == 0
		self._lock.reader_release()
		return res

	def get_char_len(self):
		"""
		Character count of all commands in buffer (ignores history)
		:return:
		"""
		self._lock.reader_acquire()
		if self.char_len < 0:
			self.char_len = sum([len(x['cmd']) for x in self.buffer_cmds])
		res = self.char_len
		self._lock.reader_release()
		return res

	def _reset_char_len(self):
		self.char_len = -1

	def __str__(self):
		self._lock.reader_acquire()
		buffer = []
		for c in self.buffer_cmds:
			buffer.append(self._item_as_str(c))
		self._lock.reader_release()
		return "AccLineBuffer: ({len}) [{buffer}]".format(len=self.get_command_count(), buffer=", ".join(buffer))

	def _item_as_str(self, item):
		item['cmd'] = item['cmd'].strip() if item is not None else None
		return "{{{id}: {cmd} (pos:{x},{y}, f:{f},i:{i},{laser})}}".format(id=item['id'], cmd=item['cmd'], x=item['x'], y=item['y'], i=item['i'], f=item['i'], laser='ON' if item['l'] else 'OFF')

	@staticmethod
	def get_cmd_from_item(cmd_obj):
		my_cmd = None
		if cmd_obj is not None:
			if isinstance(cmd_obj, basestring):
				my_cmd = cmd_obj
			else:
				my_cmd = cmd_obj.get('cmd', None) if cmd_obj else None
				my_cmd = my_cmd.rstrip() if my_cmd else my_cmd
		return my_cmd
