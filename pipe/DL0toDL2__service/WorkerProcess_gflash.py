from WorkerProcess import WorkerProcess
from dams.dl2.eventlist_v4 import Eventlist
import os
import json

class WorkerProcess_DL0toDL2(WorkerProcess):
	def __init__(self, thread_id, workermanager, processdata_shared, name="dl0dl2_process"):
		super().__init__(thread_id, workermanager, processdata_shared, name)
		# Create for eventlist
		self.eventlist_dl0 = Eventlist()

	def process_data(self, data, priority):
		super().process_data(data, priority)

		if self.supervisor.dataflowtype == "binary" or self.supervisor.dataflowtype == "filename":
			raise Exception("A string dataflowtype is expected")
			
		if self.supervisor.dataflowtype == "string":
			data = json.loads(data)
			source = os.path.join(data["path_dl0_folder"], data["filename"])
			dest = data["path_dl2_folder"]
			# Process DL0 to DL2
			self.eventlist_dl0.process_file(source, None, dest)
			# Get filename
			filename = os.path.basename(source.replace('.h5', '.dl2.h5'))
			dl2_filename = os.path.join(dest, filename)
			# Add message in queue
			self.manager.result_queue.put(dl2_filename)
