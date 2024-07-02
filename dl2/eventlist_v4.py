import os
import sys
import glob
import tables
import argparse
import numpy as np
import pandas as pd
from time import time
from tables import *
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
from multiprocessing import Pool
from scipy.signal import find_peaks
from tables.description import Float32Col
from tables.description import Float64Col

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

class Eventlist:

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
            print(f"Il file '{nome_file}' non esiste. Continuo")

    def create_directory(self, directory_path):
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            print(f"La directory '{directory_path}' è stata creata.")


    def process_file(self, filename, temperatures, outdir, log = False, startEvent=0, endEvent=-1):
        print("Processing " + filename)
        self.create_directory(outdir)

        basename = Path(outdir, os.path.basename(filename))
        outputfilename = f"{Path(basename).with_suffix('.dl2.h5')}"
        #check if file exists and is not empty
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

        #print(header)
        shape_data = -1
        lenwf = -1
        for i, data in enumerate(group):
            if i < int(startEvent):
                continue
            if endEvent > 0:
                if i > int(endEvent):
                    break
            #print(data._v_attrs._f_list("all"))
            #print(attrs)
            #tstarts.append(tstart)
            if shape_data < 0:
                if data._v_attrs.VERSION == "1.1":
                    shape_data = 1
                elif data._v_attrs.VERSION == "2.0":
                    shape_data = 0
                lenwf = len(data[:,shape_data])

            tstart = data._v_attrs.tstart

            val = np.max(data[:,shape_data])
            if val > 8192:       
                y = np.array(data[:,shape_data].shape)     
                for i, val in enumerate(data[:,shape_data]):
                    y[i] = Eventlist.twos_comp_to_int(val)
            else:
                y = data[:,shape_data]

            arr = y
            arrmov = self.moving_average(arr, 15)

            arr3 = arr[:100]
            mmean1 = arr3.mean()
            stdev1 = arr3.std()
            mmean2 = mmean1 * 2 * 0.9 

            peaks, values = find_peaks(arrmov , height=mmean2, width=15, distance=25)

            if log == True:
                print(f"Waveform num. {i} ##############################")
                print(f"la waveform num. {i} ha i seguenti peaks: {peaks} e mean value {mmean1} and stdev {stdev1}")
                #Print the original waveform
                #plt.figure()
                #plt.plot(range(len(arr)),arr, color='g')
                #plt.plot(range(len(arrmov)),arrmov)
            
            deltav = 20
        
            peaks2 = np.copy(peaks)
            #filtraggio picchi
            for v in peaks2:
                arrcalcMM = arrmov[v] - arrmov[v-deltav:v+deltav]
                #80 has been chosen with heuristics on data 
                ind = np.where(arrcalcMM[:] > 80)
                #remove peaks too small or peaks too close to the end of the wf
                if len(ind[0]) == 0 or v > 16000:
                #if  v > 16000:
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
                        
                        

            #print(f"la waveform num. {i} con peaks {peaks}")
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

                        #calculation on raw data
                        arrcalc = arr[v-deltav:]
                        #rows=np.where(arrcalc[:]>mmean1 + stdev1*5)[0]
                        rowsL = np.where(arrcalc[:] < mmean1)[0]
                        indexRows=np.where(rowsL >= deltav)[0]
                        if v < 15000 or len(indexRows) > 0:
                            arrSignal = arrcalc[0:rowsL[indexRows[0]]]
                        else:
                            arrSignal = arrcalc
                        arrSub = np.subtract(arrSignal, mmean1)
                        integral = np.sum(arrSub)
                        
                        #calculation on MM
                        arrcalcMM = arrmov[v-deltav:]
                        #rowsMM=np.where(arrcalcMM[:]>mmean1 + stdev1*5)[0]
                        rowsLMM = np.where(arrcalcMM[:] < mmean1)[0]
                        indexRowsMM=np.where(rowsLMM >= deltav)[0]
                        if v < 15000 or len(indexRowsMM) > 0:
                            arrSignalMM = arrcalcMM[0:rowsLMM[indexRowsMM[0]]]
                        else:
                            arrSignalMM = arrcalcMM
                        arrSubMM = np.subtract(arrSignalMM, mmean1)
                        integralMM = np.sum(arrSubMM)                
                        
                        #compare with exponential decay
                        arrExp = arrSubMM
                        rowsHalf=np.where(arrExp[deltav:]<=arrExp[deltav]/2.0)[0]
                        xr = range(deltav, len(arrExp)+deltav)
                        xr2 = range(len(arrExp))
                        valueE = arrExp[deltav] * np.power(2, xr2 * (-1/(rowsHalf[0])))
                        integralExp = np.sum(valueE)

                        #subtract the exponential decay for pileup
                        if len(peaks) > 1:
                            lenss = v+len(valueE)
                            if lenss > lenwf:
                                lenss = lenwf
                            ss = arrmov[v-deltav:lenss]
                            ss[deltav:lenss] = ss[deltav:lenss] - valueE[0:len(ss[deltav:lenss])]
                            ss[0:deltav] = np.full(len(ss[0:deltav] ), mmean1)

                        if log == True:
                            if j == 0:
                                plt.figure()
                                plt.plot(range(len(arr)),arr, color='g')
                                plt.plot(range(len(arrmov)),arrmov)
            
                                for v in peaks:
                                    plt.axvline(x = v, color = 'r') 
    
                                plt.show()
                            
                            plt.figure()
                            plt.plot(range(len(arrSub)),arrSub)
                            plt.plot(range(len(arrSubMM)),arrSubMM, color='black')
                            plt.axvline(x = deltav, color = 'r')
                            plt.plot(xr, valueE, color = 'r')
                            
                            print(f"integral {integral}")
                            print(f"integralMM {integralMM}")
                            print(f"integralEXP {integralExp}")
                        
                            if len(peaks) > 1:
                                plt.plot(range(len(ss)),ss-mmean1)
    
                            plt.show()

                    except:
                        print(f"EXCEPTION: Peaks non trovati nella waveform {i} del file {filename}")
                        continue


                    temp = float(self.get_temperature(tstart))


                    if len(peaks) == 1:
                        current_tstart = float(tstart)
                        f.write(f"{i}\t{0}\t{tstart}\t{peaks[0]}\t{y[peaks[0]]}\t{integral}\t{integralMM}\t{integralExp}\t{rowsHalf[0]}\t{temp:.2f}\n")
                        dl2_data.append([i, 0, current_tstart, peaks[0], y[peaks[0]], integral, integralMM, integralExp, rowsHalf[0],temp])
                    else:
                        current_tstart = float(((peaks[j] - peaks[0]) * 8e-9) + tstart)
                        f.write(f"{i}\t{j+1}\t{current_tstart}\t{peaks[j]}\t{y[peaks[j]]}\t{integral}\t{integralMM}\t{integralExp}\t{rowsHalf[0]}\t{temp:.2f}\n")
                        dl2_data.append([i, j+1, current_tstart, peaks[j], y[peaks[j]], integral, integralMM, integralExp, rowsHalf[0],temp])

                    j = j + 1

        h5file.close()
        GFhandler2.write(f"{Path(basename).with_suffix('.dl2.h5')}", dl2_data)
        
        f.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', type=str, help="input directory", required=False)
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

    if args.directory is not None:
        list_dir = glob.glob(f"{args.directory}/*.h5")
        if args.multiprocessing is None:
            for filename in list_dir:
                eventlist.process_file(filename, temperatures, args.outdir)
        #else:
        #with Pool(args.multiprocessing) as p:
        #p.map(eventlist.process_file, list_dir)

    if args.filename is not None:
        eventlist.process_file(args.filename, temperatures, args.outdir)

    #with Pool(150) as p:
    #    p.map(process_file, list_dir)

    if args.directory is None and args.filename is None:
        print("No input directory or filename have been provided")

        sys.exit(1)