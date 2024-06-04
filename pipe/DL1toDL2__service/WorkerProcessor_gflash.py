from WorkerBase import WorkerBase
from dams.dl2.eventlist_v4 import Eventlist
import os
import json
from printcolors import *

class WorkerDL1toDL2(WorkerBase):
	def __init__(self):
		super().__init__()
		# Create for eventlist
		self.eventlist = Eventlist(
			from_dl1=True,
			xml_model_path='/home/usergamma/workspace/dams/dl1/DL1model.xml'
		)

	def process_data(self, data):
		if self.supervisor.dataflowtype == "binary" or self.supervisor.dataflowtype == "filename":
			raise Exception("A string dataflowtype is expected")
			
		if self.supervisor.dataflowtype == "string":
			data = json.loads(data)
			print(f"Sent: {colore_verde}{data}{reset_colore}")
			source = data["source"]
			dest = data["dest"]
			# Process DL1 to DL2
			self.eventlist.process_file(source, None, dest)
			# Get filename
			filename = os.path.basename(source.replace('.h5', '.dl2.h5'))
			dl2_filename = os.path.join(dest, filename)
			# Add message in queue
			self.manager.result_lp_queue.put(dl2_filename)
			# self.manager.result_queue.put(dl2_filename)