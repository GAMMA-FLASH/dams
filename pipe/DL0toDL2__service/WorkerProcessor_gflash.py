from WorkerBase import WorkerBase
from dams.dl2.eventlist_v4 import Eventlist
import os
import json

class WorkerDL0toDL2(WorkerBase):
	def __init__(self):
		super().__init__()
		# Create for eventlist
		self.eventlist_dl0 = Eventlist()

	def process_data(self, data):
		if self.supervisor.dataflowtype == "binary" or self.supervisor.dataflowtype == "filename":
			raise Exception("A string dataflowtype is expected")
			
		if self.supervisor.dataflowtype == "string":
			data = json.loads(data)
			source = os.path.join(data["path_dl0_folder"], data["filename"])
			dest = data["path_dl2_folder"]
			# Process DL0 to DL2
			self.eventlist_dl0.process_file(source, None, dest, startEvent=0, endEvent=-1)
			# Get filename
			filename = os.path.basename(source.replace('.h5', '.dl2.h5'))
			dl2_filename = os.path.join(dest, filename)
			# Add message in queue
			self.manager.result_lp_queue.put(dl2_filename)
			