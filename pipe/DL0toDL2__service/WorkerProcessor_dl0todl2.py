from WorkerBase import WorkerBase
from dams.dl2.eventlist_v5 import Eventlist
import os
import json
import traceback
import sys

class WorkerDL0toDL2(WorkerBase):
	def config(self, configuration):
		# Get pid target
		pidtarget = configuration['header']['pidtarget']
		# Check if current supervisor is in the pidtarget
		if pidtarget == self.supervisor.name or pidtarget == "all".lower() or pidtarget == "*":
			# Get configuration
			self.config_detector = configuration['config']['config']
			# Check if it exists the configuration json file
			if os.path.exists(self.config_detector):
				print(f"Received config: {configuration}")
				# Init processing object
				self.eventlist_dl0 = Eventlist(
					from_dl1=False,
					config_detector=self.config_detector, 						# Config file
				)
				self.logger.debug(f"DL0toDL2 configured with - {self.config_detector}!")
			else:
				self.logger.warning(f"This configuration file {self.config_detector} for Eventlist doesn't exist!\nPlease provide a valid file!" )
				raise Exception(f"This configuration file {self.config_detector} for Eventlist doesn't exist!\nPlease provide a valid file!")
		else: 
			return
		
	def __init__(self):
		super().__init__()
		# Create for eventlist
		self.eventlist_dl0 = None

	def process_data(self, data, priority):
		self.logger.debug(f"{sys.executable}")
		if self.eventlist_dl0 is None:
			self.logger.warning("DL0toDL2 Eventlist not still configured! Please send configuration file!")
			raise Exception("DL0toDL2 Eventlist not still configured! Please send configuration file!")

		if self.supervisor.dataflowtype == "binary" or self.supervisor.dataflowtype == "filename":
			self.logger.critical(f"A string dataflowtype is expected instead of \'{self.supervisor.dataflowtype}\'", extra=self.workersname)
			raise Exception("A string dataflowtype is expected")
			
		if self.supervisor.dataflowtype == "string":
			self.logger.debug(f"Received \'{data}\'", extra=self.workersname)
			data = json.loads(data)
			source = os.path.join(data["path_dl0_folder"], data["filename"])
			dest = data["path_dl2_folder"]
			# Process DL0 to DL2
			self.logger.info(f"Starting processing \'{source}\'", extra=self.workersname)
			try:
				self.eventlist_dl0.process_file(source, None, dest, startEvent=0, endEvent=-1, pbar_show=False)
				self.logger.info(f"Processing complete \'{source}\'", extra=self.workersname)
				# Get filename
				filename = os.path.basename(source.replace('.h5', '.dl2.h5'))
				dl2_filename = os.path.join(dest, filename)
				# Add message in queue
				return dl2_filename
			except Exception as e:
				self.logger.critical(f"Exception raised:\n\tfile: \'{source}\'\n{traceback.format_exc()}", extra=self.workersname)
				return None