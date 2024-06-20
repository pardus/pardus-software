import psutil
import os

class ProcessManager():

	def __init__(self):
		self.lastpidfile = "/tmp/pardus-software-action.pid"
		self.install_cmd = "apt install -yq -o APT::Status-Fd=2"

	def get_running_process(self):
		for p in psutil.process_iter():
			# try to find active process
			cmd_string = (" ".join(p.cmdline()))
			if (self.install_cmd in cmd_string):
				return p
		return None

	def is_running_process(self, pid):
		for p in psutil.process_iter():
			if int(pid) == int(p.pid):
				return True
		return False

	def package_name(self, string):
		if self.install_cmd in string:
			return string.split(self.install_cmd)[1]

		return None

	def write_last_pid(self, value = ""):
		with open(self.lastpidfile, 'w') as file:
			file.write(str(value))

	def get_last_pid(self):
		if os.path.isfile(self.lastpidfile):
			with open(self.lastpidfile, 'r') as file:
				data = file.readline()
				if not data:
					return None
				if not self.is_running_process(data):
					return None

				return data
		return None