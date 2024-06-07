from WorkerBase import WorkerBase
from dams.dl2.eventlist_v4 import Eventlist
import os
import json
from printcolors import *
import traceback

class WorkerDL1toDL2(WorkerBase):
	def __init__(self):
		super().__init__()
		# Create for eventlist
		self.eventlist = Eventlist(
			from_dl1=True,
			xml_model_path='/home/usergamma/workspace/dams/dl1/DL1model.xml'
		)

	def process_data(self, data, priority):
		if self.supervisor.dataflowtype == "binary" or self.supervisor.dataflowtype == "filename":
			self.logger.critical(f"A string dataflowtype is expected instead of \'{self.supervisor.dataflowtype}\'", extra=self.globalname)
			raise Exception("A string dataflowtype is expected")
			
		if self.supervisor.dataflowtype == "string":
			self.logger.debug(f"\'{data}\'", extra=self.globalname)
			try:
				print(data)
				data = json.loads(data)
				source = data["source"]
				dest = data["dest"]
				# Process DL1 to DL2
				self.logger.info(f"Starting processing \'{source}\'", extra=self.globalname)
				self.eventlist.process_file(source, None, dest)
				self.logger.info(f"Processing complete \'{source}\'", extra=self.globalname)
				# Get filename
				filename = os.path.basename(source.replace('.h5', '.dl2.h5'))
				dl2_filename = os.path.join(dest, filename)
				self.logger.debug(f"dl2_filename=\'{dl2_filename}\'", extra=self.globalname)
				# Add message in queue
				# self.manager.result_lp_queue.put(dl2_filename)
				self.logger.info(f"Adding \'{dl2_filename}\' in result queue", extra=self.globalname)
				return dl2_filename
			except Exception as e:
				self.logger.critical(f"Exception raised:\n{traceback.format_exc()}", extra=self.globalname)
				return None