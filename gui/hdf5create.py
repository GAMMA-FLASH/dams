import os
import sys
import glob
import tables
import pickle
import logging
import datetime
import traceback
import numpy as np
import json
import pymysql.cursors
from tables import *
import zerosuppression
from time import time
from config_db import get_config
from Logger import Logger
from waveform import Waveform
from multiprocessing import Process


class Hdf5Create():

    def __init__(self, outdir, nwfs) -> None:
        self.waveforms = []
        self.logger = Logger().getLogger(__name__)
        conf_dict = get_config()
        self.outdir = outdir
        self.nwfs = nwfs

        self.conn = pymysql.connect(host=conf_dict["db_host"], user=conf_dict["db_user"], \
            password=conf_dict["db_pass"], db=conf_dict["db_results"], \
            port=int(conf_dict["db_port"]), cursorclass=pymysql.cursors.DictCursor)

        self.cursor = self.conn.cursor()


    def wf_append(self, wf):
        self.waveforms.append(wf)

        if len(self.waveforms) == self.nwfs:
            self.hdf5wf_create()

    def f(self, q):
        while True:
            wform = q.get()
            #self.logger.warning("ricevuta wform")
            self.wf_append(wform)

    def hdf5wf_create(self):
        """
        directory and HDF55 file creation:
        
        path for waveforms:
        /../sessionID/progress/wf_runID_subrun_configID_date.h5

        path for housekeeping:
        /../sessionID/progress/hk_runID_subrun_configID_date-h5

        """
        try:
            #getting metadata to first waveform in order to write hfd5 file
            first_wf = self.waveforms[0]
            date = first_wf.tstart
            dateUTC = datetime.datetime.utcfromtimestamp(date).strftime('%Y-%m-%dT%H_%M_%S.%f')
            sessionID = first_wf.sessionID
            runID = first_wf.runID
            configID = first_wf.configID
            rpId = first_wf.rpId


            
            dl0path = self.outdir


            filename = f"/{dl0path}/wf_runId_{str(runID).zfill(5)}_configId_{str(configID).zfill(5)}_{dateUTC}.h5"
            os.makedirs(f"/{dl0path}/", exist_ok=True)

            self.logger.warning(f"Producing HDF5: {filename}")
            h5file = open_file(filename, mode="w", title="dl0")

            group = h5file.create_group("/", 'waveforms', 'waveforms information')

            atom = tables.Int16Atom()
            shape = (16384, 1)
            filters = tables.Filters(complevel=5, complib='zlib')

            for i, wf in enumerate(self.waveforms):
                arraysy = h5file.create_carray(group, f"wf_{str(i).zfill(6)}", atom, shape, f"wf_{i}", filters=filters)
                ##### METADATA #######
                arraysy._v_attrs.VERSION = "2.0"
                arraysy._v_attrs.rp_id = wf.rpId
                arraysy._v_attrs.runid = wf.runID
                arraysy._v_attrs.sessionID = wf.sessionID
                arraysy._v_attrs.configID = wf.configID
                arraysy._v_attrs.TimeSts = wf.timeSts
                arraysy._v_attrs.PPSSliceNO = wf.ppsSliceNo
                arraysy._v_attrs.Year = wf.year
                arraysy._v_attrs.Month = wf.month
                arraysy._v_attrs.Day = wf.day
                arraysy._v_attrs.HH = wf.hh
                arraysy._v_attrs.mm = wf.mm
                arraysy._v_attrs.ss = wf.ss
                arraysy._v_attrs.usec = wf.usec
                arraysy._v_attrs.Eql = wf.eql
                arraysy._v_attrs.Dec = wf.dec
                arraysy._v_attrs.CurrentOffset = wf.curr_off
                arraysy._v_attrs.TriggerOffset = wf.trig_off
                arraysy._v_attrs.SampleNo = wf.sample_no
                arraysy._v_attrs.tstart = wf.tstart
                arraysy._v_attrs.tend = wf.tstop
                

                arraysy[:16384] = np.transpose(np.array([wf.sigr.astype(np.int16)*-1]))[:16384]

            
                if i == 1: #we select only waveform 1 for quicklook analysis in gui
                    dict_wf = {"x": wf.sigt.tolist(), "y": (wf.sige*-1).tolist()}
                    json_wf = json.dumps(dict_wf)

                    query = f"UPDATE gammaflash_test.waveform_dl1 SET waveform='{json_wf}' WHERE RedpitayaID=1;"

                    self.cursor.execute(query)

                    self.conn.commit()
            
            h5file.close()
            self.logger.warning(f"Written new HDF5: {filename}")

            okfile = open(f"{filename}.ok", "w")
            #self.logger.warning("Starting zerosoppression algorithm")
            #zerosuppression.CONVERT(filename,f"rpg{rpId}", "/data/archive/output_zs", Threshold=20, TFile="/data/gammaflash_repos/gammaflash-gui-dash/gui/weather_station/weather_station_temp.txt")
            #self.process = Process(target=zerosuppression.CONVERT, args=(filename, f"rpg{rpId}", "/data/archive/output_zs", 20, "/data/gammaflash_repos/gammaflash-gui-dash/gui/weather_station/weather_station_temp.txt"))
            #self.process.start()
            self.waveforms = []
            
            
            
        except Exception as e:
            self.logger.critical(f"{e}")
            self.logger.critical(f"{traceback.print_exc()}")
            
        
        
        





