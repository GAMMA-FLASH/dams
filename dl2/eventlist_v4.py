import os
import sys
sys.path.append('../dl1')
import glob
import tables
import argparse
import numpy as np
import pandas as pd
from time import time
from tables import *
import h5py
from pathlib import Path
from tqdm import tqdm
import traceback
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
from multiprocessing import Pool
from scipy.signal import find_peaks
from tables.description import Float32Col
from tables.description import Float64Col

from dl1_utils import DL1UtilsAtts

class GFTable(IsDescription):
    #N_Waveform\tmult\ttstart\tindex_peak\tpeak\tintegral1\tintegral2\tintegral3\thalflife\ttemp
    n_waveform = Float32Col()
    mult = Float32Col()
    tstart = Float64Col()
    index_peak = Float32Col()
    peak = Float32Col()
    integral1 = Float32Col()
    integral2 = Float32Col()
    integral3 = Float32Col()
    halflife = Float32Col()
    temp = Float32Col()

class GFhandler2:
    """
    def __init__(self, readingString=""):
        self.readingString = readingString
        self.logger = PipeLoggerConfig().getLogger(__name__)
    """
    @staticmethod
    def write(filename, data):
        
        start = time()
        
        h5file = tables.open_file(filename, "w", title="dl2")

        group = h5file.create_group("/", 'dl2', 'dl2 eventlist')
        """
        atom = tables.Float32Atom()
        shape = np.shape(data)
        filters = tables.Filters(complevel=5, complib='zlib')
        events = h5file.create_carray(group, f'eventlist', atom, shape, f"{filename}", filters=filters)
        events[:] = data[:]
        """

        table = h5file.create_table(group, 'eventlist', GFTable, "eventlist")
        gfData = table.row

        for i in range(len(data)):
            gfData["n_waveform"] = data[i][0]
            gfData["mult"] = data[i][1]
            gfData["tstart"] = data[i][2]
            gfData["index_peak"] = data[i][3]
            gfData["peak"] = data[i][4]
            gfData["integral1"] = data[i][5]
            gfData["integral2"] = data[i][6]
            gfData["integral3"] = data[i][7]
            gfData["halflife"] = data[i][8]
            gfData["temp"] = data[i][9]
            gfData.append()



        table.flush()

        h5file.close()

        #fileOk = f"{filename}.ok"

        #with open(fileOk, "w") as fok:
        #    fok.write("")

        #self.logger.debug(f" Wrote {filename} and '.ok' file. Took {round(time()-start,5)} sec")

class EventlistGeneral:
    def __init__(self) -> None:
        self.dl0_peaks = None
        self.version = None

    def moving_average(self, x, w):
        return np.convolve(x, np.ones(w), 'valid') / w
    
    @staticmethod
    def twos_comp_to_int(val, bits=14):
        if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
            val = val - (1 << bits)        # compute negative value
        return val

    def process_temps_file(self, filename):

        #when reading the temperature file we must skip row with > 2 columns and drop error rows
        df = pd.read_csv(filename, names=["Time", "Temperature"], sep=',', on_bad_lines="skip")
        df = df.dropna()
        #reconvert column in float because pandas use strings due to the error messages
        df = df.astype({"Time":np.float64, "Temperature":np.float32})

        return df
        
    def get_temperature(self, tstart):
        if self.temperatures is None:
            temp = -300
        else:
            #print(tstart)
            query = self.temperatures.query(f'{tstart} <= Time <= {tstart+30}')
            if query.empty:
                temp = -400
            else:
                temp = np.round(query["Temperature"].mean(), decimals=2)
        return temp

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

class EventlistDL0(EventlistGeneral):
    def process_file(self, filename, temperatures, outdir, log = False, startEvent=0, endEvent=-1, pbar_show=False):
        print("Processing " + filename)
        self.create_directory(outdir)
        basename = Path(outdir, os.path.basename(filename))
        outputfilename = f"{Path(basename).with_suffix('.dl2.h5')}"
        # Check if file exists and is not empty
        self.delete_empty_file(outputfilename)
        if os.path.exists(outputfilename):
            return
        h5file = open_file(filename, mode="r")
        self.temperatures = temperatures
        group = h5file.get_node("/waveforms")
        tstarts = []
        header = f"N_Waveform\tmult\ttstart\tindex_peak\tpeak\tintegral1\tintegral2\tintegral3\thalflife\ttemp"
        f = open(f"{Path(basename).with_suffix('.dl2.txt')}", "w")
        f.write(f"{header}\n")
        dl2_data = []
        
        shape_data = -1
        lenwf = -1
        for i, data in tqdm(enumerate(group), disable=not pbar_show, 
                            total=endEvent+1 if endEvent > 0 else group._g_getnchildren()):
            if i < int(startEvent):
                continue
            if endEvent > 0:
                if i > int(endEvent):
                    break
            # Get shape data
            if shape_data < 0:
                if data._v_attrs.VERSION == "1.1":
                    shape_data = 1
                elif data._v_attrs.VERSION == "2.0":
                    shape_data = 0
            lenwf = len(data[:,shape_data])
            # Get tstart
            tstart = data._v_attrs.tstart
            # Get max value in wf
            val = np.max(data[:,shape_data])
            if val > 8192:
                y = np.array(data[:,shape_data].shape)     
                for i, val in enumerate(data[:,shape_data]):
                    y[i] = Eventlist.twos_comp_to_int(val)
            else:
                y = data[:,shape_data]
            # Deep copy of y array 
            arr = y.copy()
            # Compute moving average
            arrmov = self.moving_average(arr, 15)
            # Extract peaks
            arr3 = arr[:100].copy()
            mmean1 = arr3.mean()
            stdev1 = arr3.std()
            mmean2 = mmean1 * 2 * 0.9 
            peaks, _ = find_peaks(arrmov, height=mmean2, width=15, distance=25)
            deltav = 20
            peaks2 = np.copy(peaks)
            # Filtering peaks
            for v in peaks2:
                arrcalcMM = arrmov[v] - arrmov[v-deltav:v+deltav].copy()
                # 80 has been chosen with heuristics on data 
                ind = np.where(arrcalcMM[:] > 80)
                # Remove peaks too small or peaks too close to the end of the wf
                if len(ind[0]) == 0 or v > 16000:
                    if log == True:
                        print("delete peak")
                        print(peaks)
                        plt.figure()
                        plt.plot(range(len(arr)),arr, color='g')
                        plt.plot(range(len(arrmov)),arrmov)
                        for v in peaks:
                            plt.axvline(x = v, color = 'r') 
                        plt.show()
                    peaks = peaks[peaks != v]
            if log == True:
                print(f"Waveform num. {i} ##############################")
                print(f"la waveform num. {i} ha i seguenti peaks: {peaks} e mean value {mmean1} and stdev {stdev1}")

            if len(peaks) == 0:
                current_tstart = tstart
                temp = self.get_temperature(tstart)
                f.write(f"{i}\t{0}\t{tstart}\t{-1}\t{-1}\t{-1}\t{-1}\t{-1}\t{-1}\t{temp:.2f}\n")
                dl2_data.append([i, 0, tstart, -1, -1, -1, -1, -1, -1, temp])
                if log == True:
                    print(f"{i}\tEMPTY")
                    plt.figure()
                    plt.plot(range(len(arr)),arr, color='g')
                    plt.plot(range(len(arrmov)),arrmov)
                    plt.show()
            else:
                j=0
                for v in peaks:
                    integral = 0
                    integralMM = 0
                    integralExp = 0
                    rowsHalf = [0]
                    try:
                        # Calculation on raw data
                        arrcalc = arr[v-deltav:].copy()
                        blocks_size = 25
                        arrcalc_blocks = np.lib.stride_tricks.sliding_window_view(arrcalc, blocks_size)
                        meanblock  = arrcalc_blocks.mean(axis=1)
                        rowsL = np.where(np.logical_and(meanblock > mmean1 - stdev1, 
                                                        meanblock < mmean1 + stdev1))[0]
                        if len(rowsL) > 0:
                            # Since sliding windows have stride 1, mean_block indices are 0:(len(arr)-block_size)
                            # So to index arr_calc you can use rowsL[0] directly
                            arrSignal = arrcalc[:rowsL[0]].copy()
                        else:
                            arrSignal = arrcalc.copy()
                        arrSub = np.subtract(arrSignal, mmean1)
                        integral = np.sum(arrSub)
                        # Calculation on MM
                        arrcalcMM = arrmov[v-deltav:].copy()
                        arrcalcMM_blocks = np.lib.stride_tricks.sliding_window_view(arrcalcMM, blocks_size)
                        meanblockMM  = arrcalcMM_blocks.mean(axis=1)
                        rowsLMM = np.where(np.logical_and(meanblockMM > mmean1 - stdev1, 
                                                          meanblockMM < mmean1 + stdev1))[0]
                        if len(rowsLMM) > 0:
                            arrSignalMM = arrcalcMM[:rowsLMM[0]].copy()
                        else:
                            arrSignalMM = arrcalcMM.copy()
                        arrSubMM = np.subtract(arrSignalMM, mmean1)
                        integralMM = np.sum(arrSubMM)
                        # Compare with exponential decay
                        arrExp = arrSubMM.copy()
                        rowsHalf=np.where(arrExp[deltav:]<=arrExp[deltav]/2.0)[0]
                        xr = range(deltav, len(arrExp)+deltav)
                        xr2 = range(len(arrExp))
                        valueE = arrExp[deltav] * np.power(2, xr2 * (-1/(rowsHalf[0])))
                        integralExp = np.sum(valueE)
                        # Subtract the exponential decay for pileup
                        if len(peaks) > 1:
                            lenss = v+len(valueE)
                            if lenss > lenwf:
                                lenss = lenwf
                            # NOTE: togliendo .copy() arrmov cambia. Con lui cambiano anche i plots e i valori degli integrali.
                            #       in teoria non dovrebbe cambiare nulla, ma ChatGPT suggerisce che talvolta quando due array 
                            #       condividono lo stesso spazio in memoria alcune operazioni anche se non eseguono accessi diretti
                            #       potrebbero modificarne il valore associato 
                            ss = arrmov[v-deltav:lenss].copy()
                            ss[deltav:lenss] = ss[deltav:lenss] - valueE[0:len(ss[deltav:lenss])]
                            ss[0:deltav] = np.full(len(ss[0:deltav]), mmean1)
                        # Plot arr, arrmov and peaks
                        if log == True:
                            if j == 0:
                                plt.figure()
                                plt.plot(np.arange(len(arr)), arr, color='g', label='arr')
                                plt.plot(np.arange(len(arr))[:len(arrmov)], arrmov, label='arrmov')
                                for v in peaks:
                                    plt.axvline(x = v, color = 'r', label='peaks')
                                plt.legend()
                                plt.show()
                            # Print integrals
                            print(f"integral {integral}")
                            print(f"integralMM {integralMM}")
                            print(f"integralEXP {integralExp}")
                            # Plot comparison peaks with exponential decay
                            plt.figure()
                            plt.plot(range(len(arrSub)),arrSub, label='arrSub')
                            plt.plot(range(len(arrSubMM)),arrSubMM, label='arrSubMM', color='black')
                            plt.axvline(x=deltav, label='peak', color = 'r')
                            plt.plot(xr, valueE, label='exponantial decay', color = 'r')
                            if len(peaks) > 1:
                                plt.plot(range(len(ss)),ss-mmean1, label='ss-mmean1')
                            plt.legend()
                            plt.show()
                    except Exception as e:
                        print(f"EXCEPTION: Peaks non trovati nella waveform {i} del file {filename}")
                        traceback.print_exception(e)
                        continue
                    # Get temperatures
                    temp = float(self.get_temperature(tstart))
                    # Wirte on files results
                    if len(peaks) == 1:
                        current_tstart = float(tstart)
                        # f.write(f"{i}\t{0}\t{tstart}\t{data[0]}\t{y[peaks[0]]}\t{integral}\t{integralMM}\t{integralExp}\t{rowsHalf[0]}\t{temp:.2f}\n")
                        f.write(f"{i}\t{0}\t{tstart}\t{peaks[0]}\t{y[peaks[0]]}\t{integral}\t{integralMM}\t{integralExp}\t{rowsHalf[0]}\t{temp:.2f}\n")
                        dl2_data.append([i, 0, current_tstart, peaks[0], y[peaks[0]], integral, integralMM, integralExp, rowsHalf[0],temp])
                    else:
                        current_tstart = float(((peaks[j] - peaks[0]) * data._v_attrs.Dec * 8e-9) + tstart)
                        f.write(f"{i}\t{j+1}\t{current_tstart}\t{peaks[j]}\t{y[peaks[j]]}\t{integral}\t{integralMM}\t{integralExp}\t{rowsHalf[0]}\t{temp:.2f}\n")
                        dl2_data.append([i, j+1, current_tstart, peaks[j], y[peaks[j]], integral, integralMM, integralExp, rowsHalf[0],temp])
                    j = j + 1
        h5file.close()
        GFhandler2.write(f"{Path(basename).with_suffix('.dl2.h5')}", dl2_data)
        f.close()

class EventlistDL1(EventlistGeneral):
    def __init__(self, xml_model_path: str) -> None:
        super().__init__()
        self.dl1attrs = DL1UtilsAtts(xml_model_path)

    def __getPeaks(self, peaks, wf_start):
        start_off = wf_start
        self.dl0_peaks = [pk + start_off for pk in peaks]
        return self.dl0_peaks
    
    def __getXrange(self, wf_start, wf_size):
        return np.arange(wf_start, wf_size + wf_start)

    def __getPKindex(self, j, n_peaks, peak_idx):
        if n_peaks == 1:
            return 0
        else:
            # NOTE: in DL0 wf with more than a PK get a +1
            return peak_idx + j + 1

    def process_file(self, filename, temperatures, outdir, log = False, startEvent=0, endEvent=-1, pbar_show=False):
        print("Processing " + filename)
        self.create_directory(outdir)
        basename = Path(outdir, os.path.basename(filename))
        outputfilename = f"{Path(basename).with_suffix('.dl2.h5')}"
        # Check if file exists and is not empty
        self.delete_empty_file(outputfilename)
        if os.path.exists(outputfilename):
            return
        # Open h5file
        h5file = h5py.File(filename, mode='r')
        self.temperatures = temperatures
        group = h5file["/waveforms"]
        # Get dataset
        wfs = group["wfs"]
        header = f"N_Waveform\tmult\ttstart\tindex_peak\tpeak\tintegral1\tintegral2\tintegral3\thalflife\ttemp"
        f = open(f"{Path(basename).with_suffix('.dl2.txt')}", "w")
        f.write(f"{header}\n")
        dl2_data = []

        # readapt endEvent
        endEvent = endEvent if endEvent >= 0 else len(wfs)
        for i in tqdm(range(len(wfs)), disable=not pbar_show):
            original_wf     = self.dl1attrs.get_attr(h5file, i, 'original_wf')
            if original_wf < int(startEvent):
                continue
            if endEvent > 0:
                if original_wf > int(endEvent):
                    break
            lenwf           = self.dl1attrs.get_attr(h5file, i, 'wf_size')
            wf_start        = self.dl1attrs.get_attr(h5file, i, 'wf_start')
            isdoubleEvent   = self.dl1attrs.get_attr(h5file, i, 'isdouble')
            dec             = self.dl1attrs.get_attr(h5file, i, 'Dec')
            data  = wfs[i, :lenwf]
            # Get tstart
            tstart          = self.dl1attrs.get_attr(h5file, i, 'tstart')
            mmean1          = self.dl1attrs.get_attr(h5file, i, 'mmean1')
            stdev1          = self.dl1attrs.get_attr(h5file, i, 'stdev1')
            # Get maximum value of wf
            val = np.max(data)
            y = data
            if val > 8192:
                for t, val in enumerate(data):
                    y[t] = Eventlist.twos_comp_to_int(val)
            # Deep copy of y array 
            arr = y.copy()
            # Compute moving average
            arrmov = self.moving_average(arr, 15)
            if self.dl1attrs.get_attr(h5file, i, 'n_peaks') == 0:
                # If in DL1 we didn't find any peak the list should be empty
                peaks = []
            elif isdoubleEvent:
                # If it is a double event
                peaks, _ = find_peaks(arrmov, height=mmean1*2* 0.9, width=15, distance=25)
            else:
                # If it is a single event event 
                peaks  = [self.dl1attrs.get_attr(h5file, i, 'peak_pos') - wf_start]
            deltav = 20
            peaks2 = np.copy(peaks)
            for v in peaks2:
                arrcalcMM = arrmov[v] - arrmov[v-deltav:v+deltav].copy()
                # 80 has been chosen with heuristics on data 
                ind = np.where(arrcalcMM[:] > 80)
                # Remove peaks too small or peaks too close to the end of the wf
                if len(ind[0]) == 0 or v > 16000:
                    if log == True:
                        print("delete peak")
                        print(peaks)
                        plt.figure()
                        plt.plot(range(len(arr)),arr, color='g')
                        plt.plot(range(len(arrmov)),arrmov)
                        for v in peaks:
                            plt.axvline(x = v, color = 'r') 
                        plt.show()
                    peaks = peaks[peaks != v]
            if log == True:
                print(f"Waveform num. {original_wf} ##############################")
                print(f"la waveform num. {original_wf} ha i seguenti peaks: {self.__getPeaks(peaks, wf_start)} e mean value {mmean1} and stdev {stdev1}")
            
            if len(peaks) == 0:
                current_tstart = tstart
                temp = self.get_temperature(tstart)
                f.write(f"{original_wf}\t{0}\t{tstart}\t{-1}\t{-1}\t{-1}\t{-1}\t{-1}\t{-1}\t{temp:.2f}\n")
                dl2_data.append([original_wf, 0, tstart, -1, -1, -1, -1, -1, -1, temp])
                if log == True:
                    print(f"{original_wf}\tEMPTY")
                    plt.figure()
                    plt.plot(range(len(arr)),arr, color='g')
                    plt.plot(range(len(arrmov)),arrmov)
                    plt.show()
            else:
                j=0
                for v in peaks:
                    integral = 0
                    integralMM = 0
                    integralExp = 0
                    rowsHalf = [0]
                    try:
                        # Calculation on raw data
                        arrcalc = arr[v-deltav:].copy()
                        blocks_size = 25
                        arrcalc_blocks = np.lib.stride_tricks.sliding_window_view(arrcalc, blocks_size)
                        meanblock  = arrcalc_blocks.mean(axis=1)
                        rowsL = np.where(np.logical_and(meanblock > mmean1 - stdev1, 
                                                        meanblock < mmean1 + stdev1))[0]
                        if len(rowsL) > 0:
                            # Since sliding windows have stride 1, mean_block indices are 0:(len(arr)-block_size)
                            # So to index arr_calc you can use rowsL[0] directly
                            arrSignal = arrcalc[:rowsL[0]].copy()
                        else:
                            arrSignal = arrcalc.copy()
                        arrSub = np.subtract(arrSignal, mmean1)
                        integral = np.sum(arrSub)
                        # Calculation on MM
                        arrcalcMM = arrmov[v-deltav:].copy()
                        arrcalcMM_blocks = np.lib.stride_tricks.sliding_window_view(arrcalcMM, blocks_size)
                        meanblockMM  = arrcalcMM_blocks.mean(axis=1)
                        rowsLMM = np.where(np.logical_and(meanblockMM > mmean1 - stdev1, 
                                                          meanblockMM < mmean1 + stdev1))[0]
                        if len(rowsLMM) > 0:
                            arrSignalMM = arrcalcMM[:rowsLMM[0]].copy()
                        else:
                            arrSignalMM = arrcalcMM.copy()
                        arrSubMM = np.subtract(arrSignalMM, mmean1)
                        integralMM = np.sum(arrSubMM)                
                        # Compare with exponential decay
                        arrExp = arrSubMM.copy()
                        rowsHalf=np.where(arrExp[deltav:]<=arrExp[deltav]/2.0)[0]
                        xr = range(deltav, len(arrExp)+deltav)
                        xr2 = range(len(arrExp))
                        valueE = arrExp[deltav] * np.power(2, xr2 * (-1/(rowsHalf[0])))
                        integralExp = np.sum(valueE)
                        # Subtract the exponential decay for pileup
                        if len(peaks) > 1:
                            lenss = v+len(valueE)
                            if lenss > lenwf:
                                lenss = lenwf
                            # NOTE: togliendo .copy() arrmov cambia. Con lui cambiano anche i plots e i valori degli integrali.
                            #       in teoria non dovrebbe cambiare nulla, ma ChatGPT suggerisce che talvolta quando due array 
                            #       condividono lo stesso spazio in memoria alcune operazioni anche se non eseguono accessi diretti
                            #       potrebbero modificarne il valore associato 
                            ss = arrmov[v-deltav:lenss].copy()
                            ss[deltav:lenss] = ss[deltav:lenss] - valueE[0:len(ss[deltav:lenss])]
                            ss[0:deltav] = np.full(len(ss[0:deltav]), mmean1)
                        # Plot arr, arrmov and peaks
                        if log == True:
                            if j == 0:
                                plt.figure()
                                xr_arr = self.__getXrange(wf_start, lenwf)
                                plt.plot(xr_arr, arr, color='g', label='arr')
                                plt.plot(xr_arr[:len(arrmov)], arrmov, label='arrmov')
                                for v in self.__getPeaks(peaks, wf_start):
                                    plt.axvline(x = v, color = 'r', label='peaks')
                                plt.legend()
                                plt.show()
                            # Print integrals
                            print(f"integral {integral}")
                            print(f"integralMM {integralMM}")
                            print(f"integralEXP {integralExp}")
                            # Plot comparison peaks with exponential decay
                            plt.figure()
                            plt.plot(range(len(arrSub)),arrSub, label='arrSub')
                            plt.plot(range(len(arrSubMM)),arrSubMM, label='arrSubMM', color='black')
                            plt.axvline(x=deltav, label='peak', color = 'r')
                            plt.plot(xr, valueE, label='exponantial decay', color = 'r')
                            if len(peaks) > 1:
                                plt.plot(range(len(ss)),ss-mmean1, label='ss-mmean1')
                            plt.legend()
                            plt.show()
                    except Exception as e:
                        print(f"EXCEPTION: Peaks non trovati nella waveform {original_wf} del file {filename}")
                        traceback.print_exception(e)
                        continue
                    # Get temperatures
                    temp = float(self.get_temperature(tstart))
                    # Wirte on files results
                    original_tstart = self.dl1attrs.get_attr(h5file, i, 'tstart')
                    original_pk0    = self.dl1attrs.get_attr(h5file, i, 'pk0_pos')
                    n_peaks         = self.dl1attrs.get_attr(h5file, i, 'n_peaks')
                    peak_idx        = self.dl1attrs.get_attr(h5file, i, 'peak_idx')
                    if isdoubleEvent:
                        current_tstart = ((self.__getPeaks(peaks, wf_start)[j] - original_pk0) * dec * 8e-9) + original_tstart
                    else:
                        current_tstart  = float(self.dl1attrs.get_attr(h5file, i, 'tstart1'))
                    #
                    f.write(f"{original_wf}\t{self.__getPKindex(j, n_peaks, peak_idx)}\t{current_tstart}\t{self.__getPeaks(peaks, wf_start)[j]}\t{y[peaks[j]]}\t{integral}\t{integralMM}\t{integralExp}\t{rowsHalf[0]}\t{temp:.2f}\n")
                    dl2_data.append([original_wf, self.__getPKindex(j, n_peaks, peak_idx), current_tstart, self.__getPeaks(peaks, wf_start)[j], y[peaks[j]], integral, integralMM, integralExp, rowsHalf[0], temp])
                    j = j + 1
        h5file.close()
        GFhandler2.write(f"{Path(basename).with_suffix('.dl2.h5')}", dl2_data)
        f.close()


class Eventlist:
    def __init__(self, 
                 from_dl1: bool = False,
                 xml_model_path: str = 'none') -> None:
        self.from_dl1=from_dl1
        if not self.from_dl1:
            self.evntlist = EventlistDL0()
        else:
            self.evntlist = EventlistDL1(xml_model_path)

    def moving_average(self, x, w):
        self.evntlist.moving_average(x, w)
    
    def twos_comp_to_int(self, val, bits=14):
        self.twos_comp_to_int(val, bits=bits)

    def process_temps_file(self, filename):
        self.evntlist.process_temps_file(filename)
    
    def get_temperature(self, tstart):
        self.evntlist.get_temperature(tstart)

    def delete_empty_file(self, nome_file):
        self.evntlist.delete_empty_file(nome_file)

    def create_directory(self, directory_path):
        self.evntlist.create_directory(directory_path)

    def process_file(self, filename, temperatures, outdir, log=False, startEvent=0, endEvent=-1, pbar_show=False):
        self.evntlist.process_file(filename, temperatures, outdir, log=log, startEvent=startEvent, endEvent=endEvent, pbar_show=pbar_show)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', type=str, help="input directory", required=True)
    parser.add_argument('-t', '--temperatures', type=str, help="temperature file", required=False)
    parser.add_argument('-f', '--filename', type=str, help="h5 DL0 filename", required=False)
    parser.add_argument('-o', '--outdir', type=str, help="output directory", required=True)
    parser.add_argument('-m', '--multiprocessing', type=int, help="multiprocessing pool number", required=False)

    args = parser.parse_args()

    eventlist = Eventlist()

    if args.temperatures is not None and Path(args.temperatures).exists:
        temperatures = eventlist.process_temps_file(args.temperatures)
    else:
        temperatures = None

    if args.filename is None:
        list_dir = glob.glob(f"{args.directory}/*.h5")

        if args.multiprocessing is None:
            for filename in list_dir:
                eventlist.process_file(filename, temperatures, args.outdir)
        #else:
            #with Pool(args.multiprocessing) as p:
                #p.map(eventlist.process_file, list_dir)

    else:
        eventlist.process_file(args.filename, temperatures, args.outdir)

    #with Pool(150) as p:
    #    p.map(process_file, list_dir)
