from WorkerBase import WorkerBase
from dams.dl2.eventlist_v4 import Eventlist
import os
import json
import traceback

class WorkerDL0toDL2(WorkerBase):
	def __init__(self):
		super().__init__()
		# Create for eventlist
		self.eventlist_dl0 = Eventlist()

	def process_data(self, data, priority):
		if self.supervisor.dataflowtype == "binary" or self.supervisor.dataflowtype == "filename":
			self.logger.critical(f"A string dataflowtype is expected instead of \'{self.supervisor.dataflowtype}\'", extra=self.globalname)
			raise Exception("A string dataflowtype is expected")
			
		if self.supervisor.dataflowtype == "string":
			self.logger.debug(f"Received \'{data}\'", extra=self.globalname)
			data = json.loads(data)
			source = os.path.join(data["path_dl0_folder"], data["filename"])
			dest = data["path_dl2_folder"]
			# Process DL0 to DL2
			self.logger.info(f"Starting processing \'{source}\'", extra=self.globalname)
			try:
				self.eventlist_dl0.process_file(source, None, dest, startEvent=0, endEvent=-1)
				self.logger.info(f"Processing complete \'{source}\'", extra=self.globalname)
				# Get filename
				filename = os.path.basename(source.replace('.h5', '.dl2.h5'))
				dl2_filename = os.path.join(dest, filename)
				# Add message in queue
				# self.manager.result_lp_queue.put(dl2_filename)
				self.logger.info(f"Adding \'{dl2_filename}\' in result queue", extra=self.globalname)
				return dl2_filename
			except Exception as e:
				self.logger.critical("Exception raised:\n{traceback.format_exc()}", extra=self.globalname)
				return None