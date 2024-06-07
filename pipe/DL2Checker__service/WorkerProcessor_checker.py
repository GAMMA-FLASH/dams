from WorkerBase import WorkerBase
import os
import json
import h5py
from tqdm import tqdm
from printcolors import *

class WorkerDL2CCK(WorkerBase):
	def __init__(self):
		super().__init__()
		self.json_path = '/home/usergamma/workspace/test/Out'

	def check_sameDL2(self, filePath_dl0_dl2, filePath_dl1_dl2):
		# Initialize check variables  
		res_dict = {
			'cnt_pk_notfound_h50': 0,
			'cnt_pk_notfound_h51': 0,
			'cnt_len_DL0toDL2': 0,
			'cnt_len_DL1toDL2': 0,
			'diff_rows': []
		}
		#
		F_same = True
		# Check lenghts
		with h5py.File(filePath_dl0_dl2, mode='r') as h50:
			cnt_len_h50 = len(h50['dl2']['eventlist'])
			evlst0 = h50['dl2']['eventlist']
			for data0 in evlst0:
				if -1 in data0:
					res_dict['cnt_pk_notfound_h50'] += 1
		#
		res_dict['cnt_len_DL0toDL2'] = cnt_len_h50
		with h5py.File(filePath_dl1_dl2, mode='r') as h51:
			cnt_len_h51 = len(h51['dl2']['eventlist'])
			evlst1 = h51['dl2']['eventlist']
			for data1 in evlst1:
				if -1 in data1:
					res_dict['cnt_pk_notfound_h51'] += 1
		res_dict['cnt_len_DL1toDL2'] = cnt_len_h51
		#
		F_same = F_same and ((cnt_len_h50+res_dict['cnt_pk_notfound_h50']-cnt_len_h51-res_dict['cnt_pk_notfound_h51']) == 0)
		# Check values in DL2s
		with h5py.File(filePath_dl0_dl2, mode='r') as h5_0:
			with h5py.File(filePath_dl1_dl2, mode='r') as h5_1:
				evlst0 = h5_0['dl2']['eventlist']
				evlst1 = h5_1['dl2']['eventlist']
				for data0, data1 in tqdm(zip(evlst0, evlst1), total=cnt_len_h50, disable=True):
					if not data0==data1:
						F_same = F_same and False
						res_dict['diff_rows'].append({'DL0toDL2': str(data0), 'DL1toDL2': str(data1)})
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