from Supervisor import Supervisor
from DL2Checker__service.WorkerManager_checker import WorkerManager_DL2CCK
import json
import os

class Supervisor_DL2CCK(Supervisor):
	def __init__(self, config_file="config.json", name="DL2Checker"):
		super().__init__(config_file, name)

	def start_managers(self):
		manager_DL2CCK = WorkerManager_DL2CCK(0, self, "dl2ccheck_wm")
		self.setup_result_channel(manager_DL2CCK, 0)
		manager_DL2CCK.start()
		self.manager_workers.append(manager_DL2CCK)

	#Decode the data before load it into the queue. For "dataflowtype": "binary"
	def decode_data(self, data):
		return data

	#Open the file before load it into the queue. For "dataflowtype": "file"
	#Return an array of data and the size of the array
	def open_file(self, filename):
		f = [filename]
		return f, 1
