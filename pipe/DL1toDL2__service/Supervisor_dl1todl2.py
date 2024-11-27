from Supervisor import Supervisor
from DL1toDL2__service.WorkerManager_dl1todl2 import WorkerManager_DL1toDL2
import json
import os

class Supervisor_DL1toDL2(Supervisor):
	def __init__(self, config_file="config.json", name="DL1toDL2"):
		super().__init__(config_file, name)

	def start_managers(self):
		manager_GF12 = WorkerManager_DL1toDL2(0, self, "dl1dl2_wm")
		self.setup_result_channel(manager_GF12, 0)
		manager_GF12.start()
		self.manager_workers.append(manager_GF12)

	#Decode the data before load it into the queue. For "dataflowtype": "binary"
	def decode_data(self, data):
		return data

	#Open the file before load it into the queue. For "dataflowtype": "file"
	#Return an array of data and the size of the array
	def open_file(self, filename):
		f = [filename]
		return f, 1
