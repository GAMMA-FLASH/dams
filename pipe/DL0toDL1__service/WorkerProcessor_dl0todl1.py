from WorkerBase import WorkerBase
from dams.dl1.snapeventlist import EventlistSnapshot
import os
import json
import traceback

class WorkerDL0toDL1(WorkerBase):
	def __init__(self):
		super().__init__()
		# Create for eventlist
		self.snapeventlist = EventlistSnapshot(
			'/home/usergamma/workspace/dams/dl1/dl02dl1_config.json', # Config file
			'/home/usergamma/workspace/dams/dl1/DL1model.xml'		  # XML model
		)

	def process_data(self, data, priority):
		if self.supervisor.dataflowtype == "binary" or self.supervisor.dataflowtype == "filename":
			self.logger.critical(f"A string dataflowtype is expected instead of \'{self.supervisor.dataflowtype}\'", extra=self.globalname)
			raise Exception("A string dataflowtype is expected")
			
		if self.supervisor.dataflowtype == "string":
			self.logger.debug(f"Received \'{data}\'", extra=self.globalname)
			data = json.loads(data)
			source = os.path.join(data["path_dl0_folder"], data["filename"])
			dest1 = data["path_dl1_folder"]
			dest2 = data["path_dl2_folder"]
			# Process DL0 to DL1
			# self.logger.info(f"Starting processing \'{dest1}\'", extra=self.globalname)
			try:
				self.snapeventlist.process_file(source, dest1)
				self.logger.info(f"Processing complete \'{source}\'", extra=self.globalname)
				# Get filename
				filename = os.path.basename(source.replace('.h5', '.dl1.h5'))
				# Prepare data result
				data1 = {"source": os.path.join(dest1, filename),
						 "dest": dest2}
				# self.logger.debug(f"data1 source=\'{data1['source']}\'\n", extra=self.globalname 
				# 	              f"data1 dest  =\'{data1['dest']}\'")
				# Create result message
				data1 = json.dumps(data1)
				print(data1)
				# self.manager.result_lp_queue.put(data1)
				self.logger.debug(f"Adding \'{data1}\' in result queue", extra=self.globalname)
				return data1
			except Exception as e:
				self.logger.critical(f"Exception raised:\n{traceback.format_exc()}", extra=self.globalname)
				return None