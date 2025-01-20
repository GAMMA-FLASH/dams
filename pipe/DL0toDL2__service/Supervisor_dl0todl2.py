from Supervisor import Supervisor
from DL0toDL2__service.WorkerManager_dl0todl2 import WorkerManager_DL0toDL2
import json
import os

class Supervisor_DL0toDL2(Supervisor):
	def __init__(self, config_file="config.json", name="DL0toDL2"):
		super().__init__(config_file, name)
		self.start()

	def start_managers(self):
		manager_GF02 = WorkerManager_DL0toDL2(0, self, "dl0dl2_wm")
		self.setup_result_channel(manager_GF02, 0)
		manager_GF02.start()
		self.manager_workers.append(manager_GF02)
	
	#to be reimplemented ####
	#Decode the data before load it into the queue. For "dataflowtype": "binary"
	def decode_data(self, data):		
		return data

	#to be reimplemented ####
	#Open the file before load it into the queue. For "dataflowtype": "file"
	#Return an array of data and the size of the array
	def open_file(self, filename):
		f = [filename]
		return f, 1
