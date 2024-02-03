import os

class QueueManager:

	def __init__(self):
		self.tmpfile = "/tmp/pardus-software-queue.tmp"

	def save(self, queue):
		with open(self.tmpfile, "w") as file:
			data = ""
			for proc in queue:
				data += proc['name'] + "|" + proc['command'] + "\n"
			file.write(data)
			print(data)

	def load(self):
		queue = []
		if os.path.isfile(self.tmpfile):
			with open(self.tmpfile) as file:
				data = file.read().split("\n")
				for proc in data:
					if not proc: # do not include empty strings
						continue
					name, command = proc.split('|')
					queue.append({"name": name, "command": command})
		return queue