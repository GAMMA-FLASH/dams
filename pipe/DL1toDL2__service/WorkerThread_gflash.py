from WorkerThread import WorkerThread
from dams.dl2.eventlist_v4 import Eventlist
import os
import json
from printcolors import *

class WorkerThread_DL1toDL2(WorkerThread):
	def __init__(self, thread_id, workermanager, name="dl1dl2_thread"):
		super().__init__(thread_id, workermanager, name)
		# Create for eventlist
		self.eventlist = Eventlist(from_dl1=True)

	def process_data(self, data, priority):
		super().process_data(data, priority)

		if self.supervisor.dataflowtype == "binary" or self.supervisor.dataflowtype == "filename":
			raise Exception("A string dataflowtype is expected")
			
		if self.supervisor.dataflowtype == "string":
			data = json.loads(data)
			source = data["source"]
			dest = data["dest"]
			# Process DL1 to DL2
			self.eventlist.process_file(source, None, dest)
			# Get filename
			filename = os.path.basename(source.replace('.h5', '.dl2.h5'))
			dl2_filename = os.path.join(dest, filename)
			# Add message in queue
			self.manager.result_queue.put(dl2_filename)
