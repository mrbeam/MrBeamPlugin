#
# import socket
#
# class LEDstrips():
# 	def __init__(self):
# 		self.socket_file = "/var/run/mrbeam_ledstrips.sock"
# 		self.s = None
#
# 	def _connect(self):
# 		self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
# 		try:
# 			self.s.connect(self.socket_file)
# 		except socket.error as e:
# 			print "Error while connecting to socket %s" % self.socket_file
#
# 	def on_state_change(self, state):
# 		if(self.s is None):
# 			self._connect()
#
# 		try:
# 			self.s.send(state + '\x00')
# 			print "sent state " + state
# 			data = self.s.recv(1024)
# 			#self.s.close()
# 			# TODO handle broken pipe errors -> reestablish the connection
# 		except Exception as e:
# 			print "Error: %s! mrbeam_ledstrips daemon not running?" % e
# 			self.s = None