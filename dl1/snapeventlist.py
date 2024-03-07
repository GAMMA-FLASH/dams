import argparse
import os
import tables as tb
import numpy as np
from tqdm import tqdm
from scipy.signal import find_peaks
from astropy.time import Time, TimeDelta
from dl02dl1_config import *

class EventlistSnapshot():
    def __moving_average(self, x, w):
        """
        This function calculates the moving average of an array `x` using a window of width `w`.
        ### Args
        * `x`: is the data array for which you want to calculate the moving average.
        * `w`: is the width of the moving average window.
        """
        return np.convolve(x, np.ones(w), 'valid') / w
    
    def __get_peak_lists(self):
        """
        This function returns the list of peaks found in each waveform.
        """
        # Extract array
        arr = self.carray_original[:,-1].copy()
        # Compute moving average
        arrmov = self.__moving_average(arr, 15)
        #
        mmean2 = self.mmean1 * 2 * 0.9 
        # Find peaks
        peaks, _ = find_peaks(arrmov, height=mmean2, width=15, distance=25)
        # Clone the peaks
        peaks2 = np.copy(peaks)
        # Filtering the peaks
        for v in peaks2:
            arrcalcMM = arrmov[v] - arrmov[v-self.deltav:v+self.deltav].copy()
            #  
            ind = np.where(arrcalcMM[:] > self.thr_heur)
            # Remove peaks too small or peaks too close to the end of the wf
            if len(ind[0]) == 0 or v > self.thr_end_wf:
            # If  v > 16000:
                peaks = peaks[peaks != v]
        return peaks
    
    def __is_doubleevent(self, peaks):
        """
        This function filter from list of peaks only the firtst of double events and return a flag 
        `F_double` which will be 1 if there are multiple peaks for the same event and 0 otherwise.
        ### Args
        * `peaks`: list of peaks detected
        """
        # Extract array
        # arr = self.carray_original[:,-1].copy()
        # Flag for multiple peaks for the same event
        F_double = 0
        peaks_idx = np.array(range(len(peaks)))
        # Check of multiple events 
        if len(peaks) > 1:
            peaks2    = np.copy(peaks)
            for v, v1 in zip(peaks2, peaks2[1:]):
                # arrcalc = arr[v-self.deltav:].copy()
                # arrcalc_blocks = np.lib.stride_tricks.sliding_window_view(arrcalc, self.blocksSize_dblEvent)
                # meanblock = arrcalc_blocks.mean(axis=1)
                meanblock = self.meanblocks[v:].copy()
                rowsL = np.where(np.logical_and(meanblock > self.mmean1 - 1,
                                                meanblock < self.mmean1 + 1))[0]
                if len(rowsL) > 0:
                    firts_bkgblock_idx = v + rowsL[0]
                    if firts_bkgblock_idx > v1:
                        not_v1 = peaks != v1
                        peaks_idx = peaks_idx[not_v1]
                        peaks = peaks[not_v1]
                        F_double = 1
        return peaks, peaks_idx, F_double
    
    def __decompose_date(self, dt): 
        dt_str = str(dt)
        date_str, time_str = ([item for item in dt_str.split('T')])
        dt_parts = date_str.split('-')
        tm_parts, usec = ([item for item in time_str.split('.')])
        tm_parts = tm_parts.split(':')
        year   = int(dt_parts[0])-1900
        month  = int(dt_parts[1])
        day    = int(dt_parts[2])
        hh     = int(tm_parts[0])
        mm     = int(tm_parts[1])
        ss     = int(tm_parts[2])
        us     = int(usec)
        return year, month, day, hh, mm, ss, us

    def __reset_time(self, start_index, end_index, n_event=0, time_sts=0):
        """
        This function reset the time and date attributes associated to each wf extracted from the window [start_index, end_index]
        ### Args
        * `start_index`: index where starts the window of the wf
        * `end_index`: index where ends the window of the wf
        * `n_event`: peak index
        """ 
        # Get attributes
        year = self.carray_original._v_attrs.Year
        month = self.carray_original._v_attrs.Month
        day = self.carray_original._v_attrs.Day
        hh = self.carray_original._v_attrs.HH
        mm = self.carray_original._v_attrs.mm
        ss = self.carray_original._v_attrs.ss
        usec = self.carray_original._v_attrs.usec
        tstart = self.carray_original._v_attrs.tstart
        # Calculate the time unit
        tdt = self.carray_original._v_attrs.Dec * 8e-9
        # Extract trigger
        curr_off = self.carray_original._v_attrs.CurrentOffset + 1
        trig_off = self.carray_original._v_attrs.TriggerOffset
        tstart_off = (len(self.carray_original)-curr_off)+trig_off if (curr_off > trig_off) else trig_off-curr_off
        if n_event == 0:
            # If it is the first peak of the wf tstart remain the trigger time
            tdelta = 0
            tstart1 = tstart
        else:
            # Otherwise tstart corresponds to the peak time 
            tdelta = (start_index-tstart_off) * tdt
        tstart1 = tstart + tdelta
        tend1  = tstart + (end_index-tstart_off) * tdt
        if time_sts == -1:
            date_time = Time(f'{year+1900}-{month:02d}-{day:02d}T{hh:02d}:{mm:02d}:{ss:02d}.{usec:06d}', format='isot', scale='utc', precision=6)
            time_delta = TimeDelta(tdelta, format='sec')
            date_time1 = date_time + time_delta
            year1, month1, day1, hh1, mm1, ss1, usec1 = self.__decompose_date(date_time1)
        else:
            year1, month1, day1, hh1, mm1, ss1, usec1 = year, month, day, hh, mm, ss, usec
        return year1, month1, day1, hh1, mm1, ss1, usec1, tstart1, tend1

    def __f_copy_attrs(self):
        """
        This function copies the attributes of `self.carray_original` into `self.carray_new`, 
        iterating over the attributes of the first array, and manually sets them in the second.
        """
        # Get the attributes from the original carray
        original_attrs = self.carray_original.attrs
        # Copy the attributes to the new carray
        for name_attr in original_attrs._f_list():
            value_attr = original_attrs[name_attr]
            self.carray_new.attrs[name_attr] = value_attr
        self.carray_new.attrs['VERSION'] = f"3.{self.carray_original.attrs['VERSION']}"

    def __get_endindex(self, v):
        # arr = self.carray_original[:, -1].copy()
        # arrcalc = arr[v-self.deltav:].copy()
        # arrcalc_blocks = np.lib.stride_tricks.sliding_window_view(arrcalc, self.blocksSize_endindex)
        meanblock = self.meanblocks[v:].copy()
        rowsL = np.where(np.logical_and(meanblock > self.mmean1 - 1,
                                        meanblock < self.mmean1 + 1))[0]
        if len(rowsL) > 0:
            end_index = v + rowsL[0] + 2*self.blocksSize_endindex
        else:
            end_index = len(self.carray_original)
        return end_index

    def __dl02dl1(self, group_new, h5_out, idx_new):
        """
        This function transform a wf of type `dl0` to a `dl1` to save memory space capturing
        only a window around each peak in the interval `[deltac_sx-peak, peak+deltac_dx]`
        ### Args
        * `group_new`: the group of h5 file out
        * `h5_out`: the h5 file out to save 
        * `idx_new`: new wf idx to save its name 
        """
        atom = tb.Int16Atom()
        filters = tb.Filters(complevel=5, complib='zlib')
        # Extract the peaks list 
        peaks = self.__get_peak_lists()
        # Get total number of peaks considering also double events
        n_peaks = len(peaks)
        # Filter from double events and the flag for multiple events
        peaks, peaks_idx, isdouble = self.__is_doubleevent(peaks)
        if len(peaks) == 0:
            carray_name = 'wf_%s' % str(idx_new).zfill(6)
            arr = self.carray_original.read().copy()
            shape = (len(arr), 1)
            # window_array = self.carray_original.read()[start_index:end_index, -1]
            # window_array_np = window_array.astype(np.int16)*-1
            # arr = np.transpose(np.array([window_array_np]))
            # Creiamo un nuovo CArray con gli indici filtrati
            self.carray_new = h5_out.create_carray(group_new, carray_name, atom, shape, f'wf{idx_new}', filters=filters, obj=arr)
            # Copy the old attributes
            self.__f_copy_attrs()
            # Add new attributes
            self.carray_new._v_attrs.wf_size     = -1
            self.carray_new._v_attrs.wf_start    = -1 
            self.carray_new._v_attrs.n_peaks     = 0
            self.carray_new._v_attrs.pk0_pos     = -1
            self.carray_new._v_attrs.pk0_tstart  = -1
            self.carray_new._v_attrs.peak_pos    = -1
            self.carray_new._v_attrs.peak_idx    = -1
            self.carray_new._v_attrs.mmean1      = self.mmean1
            self.carray_new._v_attrs.stdev1      = self.stdev1
            self.carray_new._v_attrs.isdouble    = isdouble
            self.carray_new._v_attrs.original_wf = self.carray_original._v_name
            # Increase the new indexes of wf
            idx_new += 1
        else:
            # Iterate over each peaks list for each wf_i
            for pk_idx, pk in zip(peaks_idx, peaks):
                carray_name = 'wf_%s' % str(idx_new).zfill(6)
                # Calculate the indices to maintain
                start_index = max(pk - self.deltac_sx, 0)
                # end_index = min(pk + self.deltac_dx, len(self.carray_original))
                end_index = self.__get_endindex(pk)
                arr = self.carray_original.read().copy()[start_index:end_index]
                shape = (len(arr), 1)
                # window_array = self.carray_original.read()[start_index:end_index, -1]
                # window_array_np = window_array.astype(np.int16)*-1
                # arr = np.transpose(np.array([window_array_np]))
                # Creiamo un nuovo CArray con gli indici filtrati
                self.carray_new = h5_out.create_carray(group_new, carray_name, atom, shape, f'wf{idx_new}', filters=filters, obj=arr)
                # Copy the old attributes
                self.__f_copy_attrs()
                # Add new attributes
                self.carray_new._v_attrs.wf_size     = end_index-start_index
                self.carray_new._v_attrs.wf_start    = start_index 
                self.carray_new._v_attrs.n_peaks     = n_peaks
                self.carray_new._v_attrs.pk0_pos     = peaks[0]
                self.carray_new._v_attrs.pk0_tstart  = self.carray_original._v_attrs.tstart
                self.carray_new._v_attrs.peak_pos    = pk
                self.carray_new._v_attrs.peak_idx    = pk_idx
                self.carray_new._v_attrs.mmean1      = self.mmean1
                self.carray_new._v_attrs.stdev1      = self.stdev1
                self.carray_new._v_attrs.isdouble    = isdouble
                self.carray_new._v_attrs.original_wf = self.carray_original._v_name
                # Date and time reset attrs
                self.carray_new._v_attrs.Year, self.carray_new._v_attrs.Month, self.carray_new._v_attrs.Day,                       \
                    self.carray_new._v_attrs.HH, self.carray_new._v_attrs.mm, self.carray_new._v_attrs.ss,                         \
                    self.carray_new._v_attrs.usec, self.carray_new._v_attrs.tstart1, self.carray_new._v_attrs.tend1 =              \
                    self.__reset_time(start_index, end_index, n_event=pk_idx, time_sts=self.carray_original._v_attrs.TimeSts)
                # Increase the new indexes of wf
                idx_new += 1
        return idx_new
    
    def process_file(self, filename, outdir, startEvent=0, endEvent=-1):
        j = 0
        # Create the name of the new file of output of type dl1 
        fname_out = os.path.join(outdir, os.path.basename(filename).replace('.h5', '.dl1.h5'))
        print(fname_out)
        # Open the source file in read mode
        with tb.open_file(filename, mode='r') as h5_in:
            group = h5_in.get_node("/waveforms")
            # Open the dest file in write mode
            with tb.open_file(fname_out, mode='w', title='dl1') as h5_out:
                # Create a new group where to save the new waveforms
                group1 = h5_out.create_group('/', 'waveforms', title='dl1')
                # Iterate over each wf_i, namely the self.carray_originals
                for i, carray_original_i in tqdm(enumerate(group), 
                                              total=group._g_getnchildren()):
                    if i < startEvent:
                        continue
                    if endEvent > 0:
                        if i > int(endEvent):
                            break
                    # Compute mean and std
                    if carray_original_i._v_attrs.VERSION == "1.1":
                        shape_data = 1
                    elif carray_original_i._v_attrs.VERSION == "2.0":
                        shape_data = 0
                    self.carray_original = carray_original_i
                    arr = self.carray_original[:100,shape_data].copy()
                    self.mmean1 = arr.mean()
                    self.stdev1 = arr.std()
                    self.meanblocks = np.lib.stride_tricks.sliding_window_view(self.carray_original[:, shape_data], self.blocksSize_dblEvent)
                    self.meanblocks = self.meanblocks.mean(axis=1)
                    # 
                    j = self.__dl02dl1(group1, h5_out, j)

    def __init__(self) -> None:
        self.deltav=deltav
        self.thr_heur=thr_heur
        self.thr_end_wf=thr_end_wf
        self.blocksSize_dblEvent=blocksSize_dblEvent
        self.blocksSize_endindex=blocksSize_endindex
        self.default_endindex=default_endindex
        self.deltac_sx=deltac_sx 
        self.deltac_dx=deltac_dx
