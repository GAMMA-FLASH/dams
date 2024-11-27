from typing import List, Any

class DL1WaveformList():
    def __init__(self) -> None:
        self.wfs   = []
        self.attrs = []
    
    def len(self):
        return len(self.wfs)
    
    def getWfsAttrs(self, idx: int):
        wf_idx = self.wfs[idx]
        attrs = self.attrs[idx]
        return wf_idx, attrs
    
    def append(self,
               wfsList: List[Any], 
               attrList: List[Any]):
        self.wfs   += wfsList
        self.attrs += attrList

    def getWfList(self):
        return self.wfs
    
    def getAttrList(self):
        return self.attrs