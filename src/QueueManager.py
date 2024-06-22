# -*- coding: utf-8 -*-
"""
Created on Fri Feb 2 12:55:00 2024

@author: bariscodefxy
"""
import os

class QueueManager:

	def __init__(self, Logger):
		self.Logger = Logger
		self.tmpfile = "/tmp/pardus-software-queue.tmp"
		self.separator = "|"

	def save(self, queue):
		with open(self.tmpfile, "w") as file:
			data = ""
			for proc in queue:
				data += proc['name'] + self.separator + proc['command'] + "\n"
			file.write(data)
			self.Logger.info(data)

	def load(self):
		queue = []
		if os.path.isfile(self.tmpfile):
			with open(self.tmpfile) as file:
				data = file.read().split("\n")
				for proc in data:
					if not proc: # do not include empty strings
						continue
					name, command = proc.split(self.separator)
					queue.append({"name": name, "command": command})
		return queue