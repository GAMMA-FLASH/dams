from WorkerBase import WorkerBase
import os
import json
import h5py
from tqdm import tqdm
import pandas as pd
from printcolors import *

class WorkerDL2CCK(WorkerBase):
	def config(self, configuration):
		# Get pid target
		pidtarget = configuration['header']['pidtarget']
		# Check if current supervisor is in the pidtarget
		if pidtarget == self.supervisor.name or pidtarget == "all".lower() or pidtarget == "*":
			# Get configuration
			self.out_json_path = configuration['config']['config']
			# Check if it exists the configuration json file
			if os.path.exists(self.out_json_path):
				print(f"Received config: {self.out_json_path}")
				self.logger.debug(f"Received config: {self.out_json_path}")
			else:
				self.logger.warning(f"The outputh json path {self.out_json_path} doesn't exist!\nPlease provide a valid path!" )
				raise Exception(f"The outputh json path {self.out_json_path} doesn't exist!\nPlease provide a valid pathe!")
		else: 
			return

	def __init__(self):
		super().__init__()
		self.json_path = None

	def check_sameDL2(self, filePath_dl0_dl2, filePath_dl1_dl2):
		# Initialize check variables  
		res_dict = {
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
			res_dict['cnt_len_DL0toDL2'] = len(df0)
			res_dict['cnt_len_DL1toDL2'] = len(df1)
			res_dict['cnt_pk_notfound_h50'] = (df0 == -1).sum().sum()
			res_dict['cnt_pk_notfound_h51'] = (df1 == -1).sum().sum()

			# Verificare se i DataFrame sono uguali
			if not df0.equals(df1):
				# Trovare le righe che differiscono
				diff_mask = ~(df0 == df1).all(axis=1)
				diff_rows_df = pd.concat([df0[diff_mask], df1[diff_mask]], axis=1, keys=['DL0toDL2', 'DL1toDL2'])
				res_dict['diff_rows'] = diff_rows_df.to_dict(orient="records")

		return res_dict

	def process_data(self, data, priority):
		if self.supervisor.dataflowtype == "binary" or self.supervisor.dataflowtype == "filename":
			self.logger.critical(f'A string dataflowtype is expected', extra=self.globalname)
			raise Exception("A string dataflowtype is expected")
			
		if self.supervisor.dataflowtype == "string":
			# print(f'{colore_giallo}{data}{reset_colore}')
			json_dir = os.path.join(os.path.dirname(os.path.dirname(data)), 'json')
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
			json_file_path   = os.path.join(self.json_path, filename)
			#
			# print(f'{colore_giallo}{filePath_dl0_dl2}\n{filePath_dl1_dl2}{reset_colore}')
			# If json_file_path already wasn't still created and both 'dl1.dl2.h5' and '.dl2.h5' exists
			
			if (not os.path.exists(json_file_path)) and os.path.exists(filePath_dl0_dl2) and os.path.exists(filePath_dl1_dl2):
				print(f'Processing {filePath_dl0_dl2} vs {filePath_dl1_dl2}')
				self.logger.debug(f'Processing \'{filePath_dl0_dl2}\' vs \'{filePath_dl1_dl2}\'', extra=self.globalname)
				# print(f"{colore_verde}i file ci sono: parte il controllo{reset_colore}")
				res_dict = self.check_sameDL2(filePath_dl0_dl2, filePath_dl1_dl2)
				# Check if there are differences in the result dictionary
				if (res_dict['cnt_pk_notfound_h50'] != res_dict['cnt_pk_notfound_h51']) and \
				   (res_dict['cnt_len_DL0toDL2'] != res_dict['cnt_len_DL1toDL2']) and \
				   (len(res_dict['diff_rows']) > 0):
					with open(json_file_path, 'w') as file_json:
						json.dump(res_dict, file_json)
					print(f"{filePath_dl0_dl2} vs {filePath_dl1_dl2}:\n",
		   				  f"{colore_rosso}ATTENZIONE RILEVATA ANOMALIA! I DUE DL2 NON COINCIDONO!{reset_colore}")
					self.logger.error(f'\'{filePath_dl0_dl2}\' vs \'{filePath_dl1_dl2}\':\n\tATTENZIONE RILEVATA ANOMALIA! I DUE DL2 NON COINCIDONO!', extra=self.globalname)
				else:
					print(f"{filePath_dl0_dl2} vs {filePath_dl1_dl2}:\n",
						  f"{colore_verde}Niente da segnalare: i due DL2 coincidono!{reset_colore}")
					self.logger.info(f'\'{filePath_dl0_dl2}\' vs \'{filePath_dl1_dl2}\':\n\tNiente da segnalare: i due DL2 coincidono!', extra=self.globalname)
			else:
				print(f"{colore_giallo}I file NON ci sono o è già presente il result JSON file!{reset_colore}")
				self.logger.debug(f'\'{filePath_dl0_dl2}\' vs \'{filePath_dl1_dl2}\':\n\tI file NON ci sono o è già presente il result JSON file!', extra=self.globalname)
			return None