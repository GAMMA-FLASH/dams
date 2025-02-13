from WorkerBase import WorkerBase
import os
import json
import h5py
import numpy as np
import pandas as pd
from printcolors import *

class WorkerDL2CCK(WorkerBase):
	def __init__(self):
		super().__init__()
		self.outjson_path = os.getenv("OUTJSON_dl2COMPARISON", "/home/gamma/workspace/Out/json")


	def config(self, conf_message):
		# Get configuration
		self.outjson_path = super().config(conf_message)

		# Check if it exists the configuration json file
		if os.path.exists(self.outjson_path):
			print(f"Received config: {self.outjson_path}")
			self.logger.debug(f"Received config: {self.outjson_path}")
		else:
			self.logger.warning(f"The outputh json path {self.outjson_path} doesn't exist!\nPlease provide a valid path!")	


	def check_sameDL2(self, filePath_dl0_dl2, filePath_dl1_dl2):
		# Initialize check variables  
		res_dict = {
			'DL0toDL2_path': filePath_dl0_dl2,
			'DL1toDL2_path': filePath_dl1_dl2,
			'cnt_pk_notfound_h50': 0,
			'cnt_pk_notfound_h51': 0,
			'cnt_len_DL0toDL2': 0,
			'cnt_len_DL1toDL2': 0,
			'diff_rows': []
		}

		# Leggere i file HDF5 e ottenere i dataset DL2
		with h5py.File(filePath_dl0_dl2, mode='r') as h50, h5py.File(filePath_dl1_dl2, mode='r') as h51:
			evlst0 = h50['dl2']['eventlist'][:]
			evlst1 = h51['dl2']['eventlist'][:]

			# Convertire in DataFrame
			df0 = pd.DataFrame(evlst0)
			df1 = pd.DataFrame(evlst1)

			# Contare gli elementi di lunghezza e mancanti
			res_dict['DL0toDL2_path'] = filePath_dl0_dl2
			res_dict['DL1toDL2_path'] = filePath_dl1_dl2
			res_dict['cnt_len_DL0toDL2'] = len(df0)
			res_dict['cnt_len_DL1toDL2'] = len(df1)
			res_dict['cnt_pk_notfound_h50'] = (df0 == -1).sum().sum()
			res_dict['cnt_pk_notfound_h51'] = (df1 == -1).sum().sum()

			# Verificare se i DataFrame sono uguali
			if not df0.equals(df1):
				# Trovare le righe che differiscono
				df0, df1 = df0.align(df1, join="outer", axis=None)  # Allinea sia righe che colonne
				diff_mask = ~(df0 == df1).all(axis=1)
				diff_rows_df = pd.concat([df0[diff_mask], df1[diff_mask]], axis=1, keys=['DL0toDL2', 'DL1toDL2'])
				res_dict['diff_rows'] = diff_rows_df.to_dict(orient="records")

		return res_dict

	def convert_to_json_serializable(self, obj):
		"""Converte ricorsivamente gli elementi non serializzabili in tipi standard Python."""
		if isinstance(obj, np.integer):
			return int(obj)
		elif isinstance(obj, np.floating):
			return float(obj)
		elif isinstance(obj, tuple):
			return "_".join(map(str, obj))  # Converte tuple in stringhe
		elif isinstance(obj, dict):
			return {self.convert_to_json_serializable(key): self.convert_to_json_serializable(value) for key, value in obj.items()}
		elif isinstance(obj, list):
			return [self.convert_to_json_serializable(item) for item in obj]
		else:
			return obj


	def process_data(self, data, priority):
		if self.supervisor.dataflowtype == "binary" or self.supervisor.dataflowtype == "filename":
			self.logger.critical(f'A string dataflowtype is expected', extra=self.workersname)
			
		if self.supervisor.dataflowtype == "string":
			if 'dl1' in data:
				# DL1 to DL2
				filePath_dl0_dl2 = data.replace('.dl1.dl2.h5', '.dl2.h5')
				filePath_dl1_dl2 = data
				filename = os.path.basename(data).replace('.dl1.dl2.h5', '.json')
			else:
				# DL0 to DL2
				filePath_dl0_dl2 = data
				filePath_dl1_dl2 = data.replace('.dl2.h5', '.dl1.dl2.h5')
				filename = os.path.basename(data).replace('.dl2.h5', '.json')
			
			json_file_path   = os.path.join(self.outjson_path, filename)

			# If json_file_path already wasn't still created and both 'dl1.dl2.h5' and '.dl2.h5' exists			
			if (not os.path.exists(json_file_path)) and os.path.exists(filePath_dl0_dl2) and os.path.exists(filePath_dl1_dl2):
				#self.logger.debug(f'Processing \'{filePath_dl0_dl2}\' vs \'{filePath_dl1_dl2}\'', extra=self.workersname)
				
				# Run the comparison method for dl1.dl2.h5 and dl2.h5
				res_dict = self.check_sameDL2(filePath_dl0_dl2, filePath_dl1_dl2)
				
				# Check if there are differences in the result dictionary
				if (res_dict['cnt_pk_notfound_h50'] != res_dict['cnt_pk_notfound_h51']) or \
				   (res_dict['cnt_len_DL0toDL2'] != res_dict['cnt_len_DL1toDL2']) or \
				   (len(res_dict['diff_rows']) > 0):
					
					# Converti tutto il dizionario
					res_dict_json_safe = self.convert_to_json_serializable(res_dict)
					
					# Store the file
					with open(json_file_path, 'w') as file_json:
						json.dump(res_dict_json_safe, file_json)
					
					# Log the anomaly
					self.logger.error(f'\'{filePath_dl0_dl2}\' vs \'{filePath_dl1_dl2}\':\n\tATTENZIONE RILEVATA ANOMALIA! I DUE DL2 NON COINCIDONO!', extra=self.workersname)
				else:
					# Log Info no problem found
					self.logger.info(f'\'{filePath_dl0_dl2}\' vs \'{filePath_dl1_dl2}\':\n\tNiente da segnalare: i due DL2 coincidono!', extra=self.workersname)
			else:
				
				# Log debug message
				self.logger.debug(f'\'{filePath_dl0_dl2}\' vs \'{filePath_dl1_dl2}\':\n\tI file NON ci sono o è già presente il result JSON file!', extra=self.workersname)
		return None