from WorkerBase import WorkerBase
from dams.dl2.eventlist_v5 import Eventlist
import os
import json
from printcolors import *
import traceback

class WorkerDL1toDL2(WorkerBase):
	def __init__(self):
		super().__init__()
		self.config_detector = os.getenv("CONFIG_DETECTOR", "/home/gamma/workspace/dams/dl1/detectorconfig_PMT.json")
		self.dl1_xmlmodel    = os.getenv("DL1_MODEL", "/home/gamma/workspace/dams/dl1/DL1model.xml")
		# Create for eventlist
		self.eventlist_dl1 = Eventlist(
			from_dl1=True,
			config_detector=self.config_detector, 								# Config file
			xml_model_path=self.dl1_xmlmodel
		)


	def config(self, conf_message):
		self.config_detector = super().config(conf_message)
		# Check if it exists the configuration json file
		if os.path.exists(self.config_detector):
			# Init processing object
			self.eventlist_dl1 = Eventlist(
				from_dl1=True,
				config_detector=self.config_detector, 							# Config file
				xml_model_path='/home/gamma/workspace/dams/dl1/DL1model.xml'
			)
			self.logger.debug(f"DL1toDL2 configured with - {self.config_detector}!")
		else:
			self.logger.warning(f"This configuration file {self.config_detector} for Eventlist doesn't exist!\nPlease provide a valid file!" )
	

	def process_data(self, data, priority):
		if self.eventlist_dl1 is None:
			self.logger.warning("DL1toDL2 Eventlist not still configured! Please send configuration file!")
		
		if self.supervisor.dataflowtype == "binary" or self.supervisor.dataflowtype == "filename":
			self.logger.critical(f"A string dataflowtype is expected instead of \'{self.supervisor.dataflowtype}\'", extra=self.workersname)
			
		if self.supervisor.dataflowtype == "string":
			self.logger.debug(f"\'{data}\'", extra=self.workersname)
			try:
				data = json.loads(data)
				source = data["source"]
				dest = data["dest"]
				# Process DL1 to DL2
				self.eventlist_dl1.process_file(source, None, dest)
				self.logger.info(f"Processing complete \'{source}\'", extra=self.workersname)
				# Get filename
				filename = os.path.basename(source.replace('.h5', '.dl2.h5'))
				dl2_filename = os.path.join(dest, filename)
				self.logger.debug(f"dl2_filename=\'{dl2_filename}\'", extra=self.workersname)
				# Add message in queue
				return dl2_filename
			except Exception as e:
				self.logger.critical(f"Exception raised:\n{traceback.format_exc()}", extra=self.workersname)
				return None