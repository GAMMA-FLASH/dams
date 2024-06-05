from pathlib import Path
import os
from tqdm import tqdm
import json
import xml.etree.ElementTree as ET
import h5py
from h5py import Dataset
import numpy as np


from dl1component import DL1WaveformList
from dl0decomposer import DL0Decomposer

class EventlistSnapshot():
    def __init__(self, 
                 configfile_path: str, 
                 xmlmodel_path: str) -> None:
        with open(configfile_path, 'r') as configfile:
            config = json.load(configfile)
            self.xlen = config['xlen']
        self.configfile = configfile_path
        tree = ET.parse(xmlmodel_path)
        self.model_root = tree.getroot()
        # 
        self.dl1wflist = DL1WaveformList()

    def __decomposeWF(self, 
                      wfdl0_dataset: Dataset, 
                      wfdl0_name: str,
                      wfdl0_idx: int):
        dl0decomp = DL0Decomposer(wfdl0_dataset, wfdl0_name, wfdl0_idx, self.configfile)
        wvfrsdl1List, attrsdl1List = dl0decomp.toDL1component()
        self.dl1wflist.append(wvfrsdl1List, attrsdl1List)
   
    def __dl1Write(self, 
                   dl1path: str,
                   nchunks=8):
        chunkshape = (nchunks, self.xlen)
        # There should be just one Group "/waveforms"
        model_waveformsGroup = self.model_root.find('Group')
        model_waveformsGroup_name  = model_waveformsGroup.get('name')
        # Compute the number of waveforms
        num_waveforms = self.dl1wflist.len()
        nchunks = min(num_waveforms, nchunks)
        # Get from the xml model the list of 
        model_CArrayList = model_waveformsGroup.findall('CArray')
        # Get the data and the set of new attributes
        wfdl1 = self.dl1wflist.getWfList()
        attrsdl1 = self.dl1wflist.getAttrList()
        with h5py.File(dl1path, 'w') as output_hdf:
            # Create the same group in new DL1
            dl1Group = output_hdf.create_group(model_waveformsGroup_name)
            # Iterate over all CArray of the model
            for model_CArray in model_CArrayList:
                # Get the definition attributes of the current CArray
                model_CArray_name      = model_CArray.get('name')
                model_CArray_dtype     = model_CArray.get('dtype')
                model_CArray_complevel = int(model_CArray.get('complevel'))
                model_CArray_complib   = model_CArray.get('complib')
                # Get the list of attributes to put in the current array
                model_carrayattrs = model_CArray.findall('Attributes/Attribute')
                # Compute the number of attributes of the current array
                num_attributes = len(model_carrayattrs)
                # Extrapolate the names of of the columns
                column_names = [attr.get('name') for attr in model_carrayattrs]
                # Initialize new array
                if num_attributes == 0:
                    # Data case
                    newarray = np.zeros((num_waveforms, self.xlen))
                    chunkshape = (nchunks, self.xlen)
                else:
                    # Attributes case
                    newarray = np.zeros((num_waveforms, num_attributes))
                    chunkshape = (nchunks, num_attributes)
                # Iterate over all the new snapshot event waveforms of the ordiginal DL0 waveform
                for idx_dl1 in range(self.dl1wflist.len()):
                    if num_attributes == 0:
                        newarray[idx_dl1, :len(wfdl1[idx_dl1])] = wfdl1[idx_dl1]
                    # wfdl1, attrsdl1 = self.dl1wflist.getWfsAttrs(idx_dl1)
                    # Import the selected attributes by the xml model to the current CArray  
                    for j, model_attr in enumerate(model_carrayattrs):
                        model_attrname = model_attr.get('name')
                        attr_value = attrsdl1[idx_dl1][model_attrname]
                        newarray[idx_dl1, j] = attr_value
                # Determine the numpy dtype
                if model_CArray_dtype == 'int16':
                    np_dtype = np.int16
                elif model_CArray_dtype == 'int64':
                    np_dtype = np.int64
                elif model_CArray_dtype == 'float64':
                    np_dtype = np.float64
                else:
                    raise ValueError(f"Unsupported dtype: {model_CArray_dtype}")
                # Create the new dataset  
                dataset = dl1Group.create_dataset(
                    model_CArray_name, 
                    data=newarray,
                    dtype=np_dtype, 
                    compression=model_CArray_complib,
                    compression_opts=model_CArray_complevel,
                    chunks=chunkshape)
                # Store column names as a single attribute
                dataset.attrs['column_names'] = ','.join(column_names)
    
    def process_file(self, filename, outdir, startEvent=0, endEvent=-1, pbar_show=False):
        print("Processing " + filename)
        self.create_directory(outdir)
        basename = Path(outdir, os.path.basename(filename))
        outputfilename = f"{Path(basename).with_suffix('.dl2.h5')}"
        # Check if file exists and is not empty
        self.delete_empty_file(outputfilename)
        if os.path.exists(outputfilename):
            return
        # Create the name of the new file of output of type dl1 
        dl1_path = os.path.join(outdir, os.path.basename(filename).replace('.h5', '.dl1.h5'))
        # Open the source file in read mode
        with h5py.File(filename, mode='r') as h5_in:
            wfdl0List = h5_in["/waveforms"]
            for i, wfdl0name in tqdm(enumerate(wfdl0List),
                                     disable=not pbar_show,
                                     total=len(wfdl0List)):
                if i < int(startEvent):
                    continue
                if endEvent > 0:
                    if i > int(endEvent):
                        break
                self.__decomposeWF(wfdl0List[wfdl0name], 
                                   wfdl0name, 
                                   i)
        self.__dl1Write(dl1_path)


    def delete_empty_file(self, nome_file):
        # Verifica se il file esiste e ha lunghezza zero
        if os.path.exists(nome_file):
            if os.path.getsize(nome_file) == 0:
                try:
                    # Cancella il file
                    os.remove(nome_file)
                    print(f"Il file '{nome_file}' è stato eliminato.")
                except OSError as e:
                    print(f"Errore durante l'eliminazione del file '{nome_file}': {e}")
            else:
                print(f"Il file '{nome_file}' non empty.")
        else:
            print(f"Il file '{nome_file}' non esiste.")
            

    def create_directory(self, directory_path):
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            print(f"La directory '{directory_path}' è stata creata.")