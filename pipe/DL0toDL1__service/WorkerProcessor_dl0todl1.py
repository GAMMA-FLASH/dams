from WorkerBase import WorkerBase
from dams.dl1.snapeventlist import EventlistSnapshot
import os
import json
import traceback

DL02DL2_DETECTOR_CFG_ENV="DL02DL2_DETECTOR_CFG"
DEFAULT_CFG='/home/gamma/workspace/dams/dl1/dl02dl1_config_SiPM.json'
class WorkerDL0toDL1(WorkerBase):
	def __init__(self):
		super().__init__()
		# Create for eventlist
		self.snapeventlist = EventlistSnapshot(
			os.getenv(DL02DL2_DETECTOR_CFG_ENV, DEFAULT_CFG), # Config file
			'/home/gamma/workspace/dams/dl1/DL1model.xml'		  # XML model
		)

	def process_data(self, data, priority):
		if self.supervisor.dataflowtype == "binary" or self.supervisor.dataflowtype == "filename":
			self.logger.critical(f"A string dataflowtype is expected instead of \'{self.supervisor.dataflowtype}\'", extra=self.workersname)
			raise Exception("A string dataflowtype is expected")
			
		if self.supervisor.dataflowtype == "string":
			self.logger.debug(f"Received \'{data}\'", extra=self.workersname)
			data = json.loads(data)
			source = os.path.join(data["path_dl0_folder"], data["filename"])
			dest1 = data["path_dl1_folder"]
			dest2 = data["path_dl2_folder"]
			# Process DL0 to DL1
			# self.logger.info(f"Starting processing \'{dest1}\'", extra=self.workersname)
			try:
				self.snapeventlist.process_file(source, dest1)
				self.logger.info(f"Processing complete \'{source}\'", extra=self.workersname)
				# Get filename
				filename = os.path.basename(source.replace('.h5', '.dl1.h5'))
				# Prepare data result
				data1 = {"source": os.path.join(dest1, filename),
						 "dest": dest2}
				# self.logger.debug(f"data1 source=\'{data1['source']}\'\n", extra=self.workersname 
				# 	              f"data1 dest  =\'{data1['dest']}\'")
				# Create result message
				data1 = json.dumps(data1)
				print(data1)
				# self.manager.result_lp_queue.put(data1)
				self.logger.debug(f"Adding \'{data1}\' in result queue", extra=self.workersname)
				return data1
			except Exception as e:
				self.logger.critical(f"Exception raised:\n{traceback.format_exc()}", extra=self.workersname)
				return None