from WorkerProcess import WorkerProcess
from dams.dl1.snapeventlist_v2 import EventlistSnapshot
import os
import json

class WorkerProcess_DL0toDL1(WorkerProcess):
	def __init__(self, thread_id, workermanager, processdata_shared, name="dl0dl1_process"):
		super().__init__(thread_id, workermanager, processdata_shared, name)
		# Create for eventlist
		self.snapeventlist = EventlistSnapshot()

	def process_data(self, data, priority):
		super().process_data(data, priority)

		if self.supervisor.dataflowtype == "binary" or self.supervisor.dataflowtype == "filename":
			raise Exception("A string dataflowtype is expected")
			
		if self.supervisor.dataflowtype == "string":
			data = json.loads(data)
			source = os.path.join(data["path_dl0_folder"], data["filename"])
			dest1 = data["path_dl1_folder"]
			dest2 = data["path_dl2_folder"]
			# Process DL0 to DL1
			self.snapeventlist.process_file(source, dest1)
			# Get filename
			filename = os.path.basename(source.replace('.h5', '.dl1.h5'))
			# Prepare data result
			data1 = {"source": os.path.join(dest1, filename),
			     	 "dest": dest2}
			# Create result message
			data1 = json.dumps(data1)
			self.manager.result_queue.put(data1)
