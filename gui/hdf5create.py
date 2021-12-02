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

            arraysy[:16384, :2] = np.transpose(np.array([wf.sigt,wf.sige*-1]))[:16384, :2]

            try: 
                if i == 1: #we select only waveform 1 for quicklook analysis in gui
                    dict_wf = {"x": wf.sigt.tolist(), "y": (wf.sige*-1).tolist()}
                    json_wf = json.dumps(dict_wf)

                    query = f"UPDATE gammaflash_test.waveform_dl1 SET waveform='{json_wf}' WHERE RedpitayaID=1;"

                    self.cursor.execute(query)

                    self.conn.commit()
            except Exception as e:
                self.logger.critical(f"{e}")
        
        h5file.close()
        okfile = open(f"{filename}.ok", "w")
        self.waveforms = []





