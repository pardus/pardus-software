"""
Created on Sat Feb 3 17:31:00 2024

@author: bariscodefxy
"""
import psutil
import os

class ProcessManager():

	def __init__(self):
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