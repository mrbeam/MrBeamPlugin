
import socket

class StateHandler():
	socket_file = "/var/run/mrbeam_state.sock"
	s = None # socket object

	def open_socket(self):
		s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		s.connect(socket_file)
		
	def on_state_change(self, state):
		if(s is None):
			open_socket()
			
		s.send(state + '\x00')
		print "sent state " + state
		data = s.recv(1024)
		s.close()