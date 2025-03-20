import json
from scipy.signal import find_peaks
import numpy as np
from h5py import Dataset

class DL0Decomposer():
    def __init__(self, 
                 wfdl0: Dataset,
                 name: str, 
                 idx: int,
                 configfile_path: str) -> None:
        with open(configfile_path, 'r') as configfile:
            config = json.load(configfile)
        # Import dynamcly the attributes from JSON object
        for key, value in config.items():
            setattr(self, key, value)

        self.wfdl0   = wfdl0
        self.idx     = idx
        self.name    = name
        #self.data    = self.wfdl0[:, -1]  + self.arr_bias
        self.data    = self.wfdl0[:, -1]
        self.mmean1  = np.mean(self.data[:self.bkgbaselev_size])
        self.stdev1  = np.std(self.data[:self.bkgbaselev_size])
        self.meanblocks = np.lib.stride_tricks.sliding_window_view(self.wfdl0[:, -1], self.blocks_size)
        self.meanblocks = self.meanblocks.mean(axis=1)
        self.wvfrsdl1List = []
        self.attrsdl1List = []
        
    def __moving_average(self, x, w): # OK
        """
        This function calculates the moving average of an array `x` using a window of width `w`.
        ### Args
        * `x`: is the data array for which you want to calculate the moving average.
        * `w`: is the width of the moving average window.
        """
        return np.convolve(x, np.ones(w), 'same') / w
    
    def __get_peak_lists(self):  # OK
        """
        This function returns the list of peaks found in each waveform.
        """
        # Extract array
        arr = self.data + self.arr_bias
        # Compute moving average
        arrmov = self.__moving_average(arr, self.mavg_wsize)
        #
        mmean2 = self.mmean1 * 2 * 0.9
        # mmean2 = self.mmean1 + self.stdev1 * 1.96 
        # Find peaks
        peaks, _ = find_peaks(arrmov, height=mmean2, width=self.findpk_width, distance=self.findpk_distance)
        # Clone the peaks
        peaks2 = np.copy(peaks)
        # Filtering the peaks
        for v in peaks2:
            arrcalcMM = arrmov[v] - arrmov[v-self.deltav:v+self.deltav]
            #  
            ind = np.where(arrcalcMM[:] > self.thr_heur)
            # Remove peaks too small or peaks too close to the end of the wf
            if len(ind[0]) == 0 or v > self.thr_end_wf or v < self.thr_start_wf:
                peaks = peaks[peaks != v]
        return peaks
    
    def __is_doubleevent(self, peaks, peaks_idx):
        """
        Filtra eventi multipli sovrapposti (pile-up) in una lista di picchi.
        Restituisce la lista filtrata, gli indici e un flag che indica la presenza di eventi multipli.
        
        Un picco viene mantenuto solo se esiste almeno un successivo il cui indice 
        è a distanza minore di `self.delta_dx` dal primo.
        
        Args:
            peaks (np.array): Lista di picchi rilevati.
            peaks_idx (np.array): Indici originali dei picchi.

        Returns:
            peaks (np.array): Lista filtrata di picchi.
            peaks_idx (np.array): Indici originali dei picchi mantenuti.
            F_double (int): Flag (1 se c'erano eventi multipli, 0 altrimenti).
        """
        if len(peaks) < 2:
            return peaks, peaks_idx, 0  # Se c'è un solo picco, non c'è pile-up

        F_double = 0
        # Lista per i picchi che soddisfano la condizione
        keep_mask = np.zeros(len(peaks), dtype=bool)

        v = peaks[0]
        for i in range(1, len(peaks)):
            endindex = self.__get_endindex(v)
            # Controlla se esiste almeno un picco successivo entro `self.delta_dx`
            if peaks[i] < endindex:
                keep_mask[i] = True

        if np.any(keep_mask):
            F_double = 1  # Almeno un evento multiplo rilevato

        peaks     = peaks[~keep_mask]
        peaks_idx = peaks_idx[~keep_mask]

        return peaks, peaks_idx, F_double

    # def __reset_time(self, start_index, end_index, n_event=0):
    def __reset_time(self, peak_first, current_peak, end_index, wf_size, pk_idx):
        """
        This function reset the time and date attributes associated to each wf extracted from the window [start_index, end_index]
        ### Args
        * `start_index`: index where starts the window of the wf
        * `end_index`: index where ends the window of the wf
        * `n_event`: peak index
        """ 
        # Get attributes
        tstart = self.wfdl0.attrs['tstart']
        # Calculate the time unit
        if 'Dec' in self.wfdl0.attrs:
            tdt = self.wfdl0.attrs['Dec'] * 8e-9
        else:
            tdt = 8e-9
        # Compute tstart1 
        deltat  = current_peak - peak_first        
        tstart1 = float(((current_peak - peak_first) * 8e-9) + tstart)
        # tstart1 = tstart + (deltat * tdt)
        deltat  = end_index - peak_first
        tend1   = tstart + (deltat * tdt)
        return tstart1, tend1

    def __attrstodict(self): # OK
        """
        This function copies the attributes of `self.carray_original` into `self.carray_new`, 
        iterating over the attributes of the first array, and manually sets them in the second.
        """
        # Get the attributes from the original carray
        dl0_attrs = self.wfdl0.attrs
        return dict(dl0_attrs)
    
    def __get_startindex(self, v):  # min_steps definisce quanti valori consecutivi devono stare nel range
        meanblock = np.copy(self.meanblocks[:v])[::-1]
        if len(meanblock) < self.deltac_sx:
            # Se non è possibile creare almeno una window
            return 0
        meandiffs = np.abs(meanblock - self.mmean1)
        condition = meandiffs < self.stdev1
        condition_ws = np.lib.stride_tricks.sliding_window_view(condition, self.deltac_sx)
        valid_indeces = np.where(condition_ws.all(axis=1))[0]
        if len(valid_indeces) > 0:
            end_index = v - (valid_indeces[0] + self.deltac_sx)
            return end_index
        else:
            # Se nessuna sequenza valida è trovata, ritorna la lunghezza massima
            return 0

    def __get_endindex(self, v):  # min_steps definisce quanti valori consecutivi devono stare nel range
        meanblock = self.meanblocks[v:]
        if len(meanblock) < self.deltac_dx:
            # Se non è possibile creare almeno una window
            return len(self.wfdl0)
        meandiffs = np.abs(meanblock - self.mmean1)
        condition = meandiffs < self.stdev1
        condition_true = np.where(condition)
        condition_ws = np.lib.stride_tricks.sliding_window_view(condition, self.deltac_dx)
        valid_indeces = np.where(condition_ws.all(axis=1))[0]
        if len(valid_indeces) > 0:
            end_index = v + valid_indeces[0] + self.deltac_dx
            return end_index
        else:
            # Se nessuna sequenza valida è trovata, ritorna la lunghezza massima
            return len(self.wfdl0)
    
    def __dl02dl1(self):
        """
        This function transform a wf of type `dl0` to a `dl1` to save memory space capturing
        only a window around each peak in the interval `[deltac_sx-peak, peak+deltac_dx]`
        """
        # Extract the peaks list 
        peaks = self.__get_peak_lists()
        # Get total number of peaks considering also double events
        n_peaks = len(peaks)
        peaks_idx = np.arange(len(peaks))
        # Filter from double events and the flag for multiple events
        peaks, peaks_idx, isdouble = self.__is_doubleevent(peaks, peaks_idx)
        if len(peaks) == 0:
            # Copy the old data and append the data
            array_new = self.wfdl0[:, -1]
            # Copy the old attributes and add new attributes
            dl1attrs = self.__attrstodict() | {
                'wf_size'     : -1,
                'wf_start'    : -1,
                'n_peaks'     : 0,
                'pk0_pos'     : -1,
                'pk0_tstart'  : -1,
                'peak_pos'    : -1,
                'peak_idx'    : -1,
                'mmean1'      : self.mmean1,
                'stdev1'      : self.stdev1,
                'isdouble'    : isdouble,
                'original_wf' : self.idx,
                'tstart1'     : -1,
                'tend1'       : -1
            }
            # Save new data and attributes
            self.wvfrsdl1List.append(array_new)
            self.attrsdl1List.append(dl1attrs)
        else:
            # Iterate over each peaks list for each wf_i
            # for pk_idx, pk in zip(peaks_idx, peaks):
            pk, peaks1 = peaks[0], np.copy(peaks[1:])
            _pki, _peaks1_idx = peaks_idx[0], np.copy(peaks_idx[1:])
            while pk != -1:
                # Calculate the indices to maintain
                # start_index = max(pk - self.deltac_sx, 0)
                start_index = self.__get_startindex(pk)
                # Calculate the endindex
                end_index = self.__get_endindex(pk)

                # Extract the sanapshot
                snapshot_arr = self.wfdl0[start_index:end_index, -1]
                wf_size = end_index-start_index
                # Add zero pad to the right 
                array_new = np.zeros(self.xlen)[:len(snapshot_arr)] + snapshot_arr
                # Date and time reset attrs
                # tstart1, tend1 = self.__reset_time(start_index, end_index, n_event=pk_idx)
                tstart1, tend1 = self.__reset_time(peaks[0], pk, end_index, wf_size, _pki)
                # Copy the old attributes and add new attributes
                dl1attrs = self.__attrstodict() | {
                    'wf_size'     : wf_size,
                    'wf_start'    : start_index ,
                    'n_peaks'     : n_peaks,
                    'pk0_pos'     : peaks[0],
                    'pk0_tstart'  : self.wfdl0.attrs['tstart'],
                    'peak_pos'    : pk,
                    'peak_idx'    : _pki,
                    'mmean1'      : self.mmean1,
                    'stdev1'      : self.stdev1,
                    'isdouble'    : isdouble,
                    'original_wf' : self.idx,
                    'tstart1'     : tstart1,
                    'tend1'       : tend1
                }
                # Save new data and attributes
                self.wvfrsdl1List.append(array_new)
                self.attrsdl1List.append(dl1attrs)
                # update step
                if len(peaks1) >= 1:
                    peaks1, _peaks1_idx, isdouble = self.__is_doubleevent(peaks1, _peaks1_idx)
                    pk, peaks1        = peaks1[0], peaks1[1:]
                    _pki, _peaks1_idx = _peaks1_idx[0], _peaks1_idx[1:]
                else:
                    pk = -1

    def toDL1component(self):
        self.__dl02dl1()
        return self.wvfrsdl1List, self.attrsdl1List
        # dl1cmp = DL1Component(self.wvfrsdl1List, self.attrsdl1List)
        # return dl1cmp 