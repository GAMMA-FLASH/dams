import h5py
import xml.etree.ElementTree as ET

class DL1UtilsAtts():
    def __init__(self,
                 xml_model_path: str) -> None:
        tree = ET.parse(xml_model_path)
        self.model_root = tree.getroot()
        # Get the CArray list
        model_CArrayList = self.model_root.find('Group').findall('CArray')
        # Define architecture for attributes
        self.attrs_ref      = []
        self.attrSet_name   = []
        self.attrs_dtype    = []
        self.attrs_names    = []
        # Extrapolate the set attributes
        for model_CArray in model_CArrayList:
            model_CArray_name      = model_CArray.get('name')
            if 'attrs' in model_CArray_name:
                model_CArray_dtype     = model_CArray.get('dtype')
                model_columns_names    = [attr.get('name') for attr in model_CArray.findall('Attributes/Attribute')]
                # Append attrubutes metadata
                self.attrSet_name.append(model_CArray_name)
                self.attrs_dtype.append(model_CArray_dtype)
                self.attrs_names.append(model_columns_names)

    def get_attr(self,
                 h5file: h5py.File, 
                 waveform_idx: int, 
                 attr: str):
        for i in range(len(self.attrs_names)):
            if attr in self.attrs_names[i]:
                attrseet    = self.attrSet_name[i]
                attrcolumns = self.attrs_names[i]
                j = attrcolumns.index(attr)
                return h5file[f"/waveforms/{attrseet}"][waveform_idx, j]
        raise ValueError(f'{attr} is not present in the list of attributes')