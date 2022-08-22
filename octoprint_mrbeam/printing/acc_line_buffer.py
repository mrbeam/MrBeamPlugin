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
        self.dirty = False

    def reset(self):
        self._lock.writer_acquire()
        self.buffer_cmds.clear()
        self.declined_cmds.clear()
        self._last_responded = None
        self._reset_char_len()
        self.id = 0
        self._lock.writer_release()

    def reset_clogged(self):
        """
        Should we find out that our counting got incorrect (e.g. we missed an 'ok' from grbl)
        this resets the command counter. Should be called only when you're sure that grbl's serial buffer is empty.
        """
        self._lock.writer_acquire()
        # we need to check again if buffer_cmds is still not empty. (We saw exceptions...!)
        if len(self.buffer_cmds) > 0:
            self._last_responded = self.buffer_cmds.pop()
        self.buffer_cmds.clear()
        self._reset_char_len()
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
            id=self.id,
            dirty=self.dirty,
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
            return None  # happens after a reset during cancellation of a job
        self._lock.writer_acquire()
        self._last_responded = self.buffer_cmds.popleft()
        self._reset_char_len()
        self._lock.writer_release()
        return self._last_responded

    def decline_cmd(self):
        """
        Removes the oldest command (item) from the buffer and keeps it as recovery command
        # TODO: if the error is not recovery, this cmd remains in memory until the next reset()
        """
        if self.is_empty():
            return None
        self._lock.writer_acquire()
        self._last_responded = self.buffer_cmds.popleft()
        self._reset_char_len()
        self.declined_cmds.append(self._last_responded)
        self._lock.writer_release()
        return self._last_responded

    def get_last_responded(self):
        """
        returns the last acknowledged command
        :return: item
        """
        self._lock.reader_acquire()
        res = self._last_responded
        self._lock.reader_release()
        return res

    def recover_next_command(self):
        res = None
        self._lock.writer_acquire()
        if self.declined_cmds:
            d = self.declined_cmds.popleft()
            res = d["cmd"].rstrip()
        self._lock.writer_release()
        return res

    def set_dirty(self):
        """
        Marks all currently waiting and all new commands as dirty until add_cleaned is called
        """
        self._lock.writer_acquire()
        self.dirty = True
        for c in self.buffer_cmds:
            c["dirty"] = True
        for c in self.declined_cmds:
            c["dirty"] = True
        self._lock.writer_release()

    def set_clean(self):
        """
        No further items will be marked as dirty. Once all dirty items left the system, it'll be seen as clean again
        """
        self._lock.writer_acquire()
        self.dirty = False
        self._lock.writer_release()

    def is_dirty(self):
        """
        Returns True if any item in any queue is marked dirty
        """
        if self.dirty:
            return True
        res = False
        self._lock.reader_acquire()
        for c in self.buffer_cmds:
            if c["dirty"]:
                res = True
                break
        if not res:
            for c in self.declined_cmds:
                if c["dirty"]:
                    res = True
                    break
        self._lock.reader_release()
        return res

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
            self.char_len = sum([len(x["cmd"]) for x in self.buffer_cmds])
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
        dec_buffer = []
        for c in self.declined_cmds:
            dec_buffer.append(self._item_as_str(c))
        self._lock.reader_release()
        return "AccLineBuffer: is_dirty: {dirty}, acc_buffer: ({len})[{buffer}], declined_cmds: ({len_declined})[{declined}]".format(
            dirty=self.is_dirty(),
            len=self.get_command_count(),
            buffer=", ".join(buffer),
            len_declined=len(self.declined_cmds),
            declined=", ".join(dec_buffer),
        )

    def _item_as_str(self, item):
        item["cmd"] = item["cmd"].strip() if item is not None else None
        return "{{{id}: {cmd}{dirty}}}".format(
            id=item["id"], cmd=item["cmd"], dirty=" !dirty!" if item["dirty"] else ""
        )

    @staticmethod
    def get_cmd_from_item(cmd_obj):
        my_cmd = None
        if cmd_obj is not None:
            if isinstance(cmd_obj, basestring):
                my_cmd = cmd_obj
            else:
                my_cmd = cmd_obj.get("cmd", None) if cmd_obj else None
                my_cmd = my_cmd.rstrip() if my_cmd else my_cmd
        return my_cmd
