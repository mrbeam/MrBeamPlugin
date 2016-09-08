
import socket

class LEDstrips():
	def __init__(self):
		self.socket_file = "/var/run/mrbeam_state.sock"
		self.s = None
		
	def _connect(self):
		self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		self.s.connect(self.socket_file)
		
		
	def on_state_change(self, state):
		if(self.s is None):
			self._connect()
			
		self.s.send(state + '\x00')
		print "sent state " + state
		data = self.s.recv(1024)
		#self.s.close()