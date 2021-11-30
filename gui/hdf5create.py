import os
import sys
import glob
import tables
import pickle
import logging
import datetime
import numpy as np
import json
import pymysql.cursors
from tables import *
from time import time
from config_db import get_config
from Logger import Logger
from waveform import Waveform
from multiprocessing import Process


N_WFORMS = 1000

class Hdf5Create():

    def __init__(self) -> None:
        self.waveforms = []
        self.logger = Logger().getLogger(__name__)
        conf_dict = get_config()

        self.conn = pymysql.connect(host=conf_dict["db_host"], user=conf_dict["db_user"], \
            password=conf_dict["db_pass"], db=conf_dict["db_results"], \
            port=int(conf_dict["db_port"]), cursorclass=pymysql.cursors.DictCursor)

        self.cursor = self.conn.cursor()


    def wf_append(self, wf):
        self.waveforms.append(wf)

        if len(self.waveforms) == N_WFORMS:
            self.hdf5wf_create()
        print(wf)

    def f(self, q):
        while True:
            wform = q.get()
            self.logger.warning("ricevuta wform")
            self.wf_append(wform)

    def hdf5wf_create(self):
        """
        directory and HDF55 file creation:
        
        path for waveforms:
        /../sessionID/progress/wf_runID_subrun_configID_date.h5

        path for housekeeping:
        /../sessionID/progress/hk_runID_subrun_configID_date-h5

        """
        first_wf = self.waveforms[0]
        date = first_wf.tstart
        dateUTC = datetime.datetime.utcfromtimestamp(date).strftime('%Y-%m-%dT%H:%M:%S.%f')
        sessionID = first_wf.sessionID[0]
        runID = first_wf.runID[0]
        configID = first_wf.configID[0]

        
        dl0path = os.environ["DL0_INPUT"]


        filename = f"/{dl0path}/{str(sessionID).zfill(5)}/wf_{str(runID).zfill(5)}_{str(configID).zfill(5)}_{dateUTC}.h5"
        os.makedirs(f"/{dl0path}/{str(sessionID).zfill(5)}/", exist_ok=True)


        h5file = open_file(filename, mode="w", title="dl0")

        group = h5file.create_group("/", 'waveforms', 'waveforms information')

        atom = tables.Float32Atom()
        shape = (16384, 2)
        filters = tables.Filters(complevel=5, complib='zlib')

        for i, wf in enumerate(self.waveforms):
            arraysy = h5file.create_carray(group, f"wf_{str(i).zfill(6)}", atom, shape, f"wf_{i}", filters=filters)
            arraysy._v_attrs.rp_id = 1
            arraysy._v_attrs.tstart = wf.tstart
            arraysy._v_attrs.tend = wf.tstop
            arraysy._v_attrs.runid = wf.runID[0]
            arraysy._v_attrs.sessionID = wf.sessionID[0]
            arraysy._v_attrs.configID = wf.configID[0]
            arraysy._v_attrs.calib = 8

            size_arrays = sys.getsizeof(wf.sigt) + sys.getsizeof(wf.sige)
            self.logger.warning(f"sizeof array is {size_arrays}")

            arraysy[:16384, :2] = np.transpose(np.array([wf.sigt,wf.sige*-1]))[:16384, :2]

            if i == 1: #we select only waveform 1 for quicklook analysis in gui
                dict_wf = {"x": wf.sigt, "y": (wf.sige*-1)}
                json_wf = json.dumps(dict_wf)

                query = f"UPDATE gammaflash_test.waveform_dl1 SET waveform='{json_wf}' WHERE RedpitayaID=1;"

                self.cursor.execute(query)

                self.conn.commit()
        
        h5file.close()
        okfile = open(f"{filename}.ok", "w")
        #self.wfTotCount = 0
        self.waveforms = []

        

if __name__ == "__main__":
    pass
    """
    filedir = sys.argv[1]

    files = glob.glob(f"{filedir}/*.bin")

    count = 0

    for i,filein in enumerate(files):


        if count == 0:
            h5file = open_file(f"dl0_{time()}.h5", mode="w", title="dl0")

            group = h5file.create_group("/", 'waves', 'waves information')
            atom = tables.Float32Atom()
            shape = (16384, 2)
            filters = tables.Filters(complevel=5, complib='zlib')
        try:
            x, y = redPitayaDataConverter(filein)
        except:
            continue
        filename = filein.split("/")[-1]

        arraysy = h5file.create_carray(group, f'{filename}', atom, shape, f"{filename}", filters=filters)
        arraysy._v_attrs.rp_id = 1
        arraysy._v_attrs.tstart = "2021-08-25T16:00:04+00:00"
        arraysy._v_attrs.tend = "2021-08-25T17:00:04+00:00"
        arraysy._v_attrs.calib = 8

        arraysy[:16384, :2] = np.transpose(np.array([x,y]))[:16384, :2]

        count +=1

        if count == 10000:
            h5file.close()
            count = 0

        #arraysx = h5file.create_array(group, f"{filein}_y", np.array(x), f"{filein}_y")
    
        table = h5file.create_table(group, f'{filename}', GfData, f"{filename}", expectedrows=16500)

        gfData = table.row
        for i in range(len(x)):
            gfData["x"] = x[i]
            gfData["y"] = y[i]

            gfData.append()
    
    table.flush
    """





