import argparse
import os
import tables as tb
import numpy as np
from tqdm import tqdm
from scipy.signal import find_peaks
from astropy.time import Time, TimeDelta
from dl02dl1_config import *

def moving_average(x, w):
    """
    This function calculates the moving average of an array `x` using a window of width `w`.
    ### Args
    * `x`: is the data array for which you want to calculate the moving average.
    * `w`: is the width of the moving average window.
    """
    return np.convolve(x, np.ones(w), 'valid') / w

def get_peak_lists(carray_i, mmean1,
                   deltav=deltav, thr_heur=thr_heur, thr_end_wf=thr_end_wf):
    """
    This function returns the list of peaks found in each waveform.
    ### Args
    * `carray_i`: The wf
    * `mmean1`: mean of first 100 samples of background of carray_original
    * `deltav`: Define the width of range around peaks
    * `thr_heur`: threshold below which a peak is discarded, it is set as default to 80 and 
                  ithas been chosen with heuristics on data
    """
    # Extract array
    arr = carray_i[:,-1].copy()
    # Compute moving average
    arrmov = moving_average(arr, 15)
    #
    arr3 = arr[:100].copy()
    mmean1 = arr3.mean()
    mmean2 = mmean1 * 2 * 0.9 
    # Find peaks
    peaks, _ = find_peaks(arrmov, height=mmean2, width=15, distance=25)
    # Clone the peaks
    peaks2 = np.copy(peaks)
    # Filtering the peaks
    for v in peaks2:
        arrcalcMM = arrmov[v] - arrmov[v-deltav:v+deltav].copy()
        #  
        ind = np.where(arrcalcMM[:] > thr_heur)
        # Remove peaks too small or peaks too close to the end of the wf
        if len(ind[0]) == 0 or v > thr_end_wf:
        # If  v > 16000:
            peaks = peaks[peaks != v]
    return peaks

def is_doubleevent(peaks, carray_i, mmean1, stdev1):
    """
    This function filter from list of peaks only the firtst of double events and return a flag 
    `F_double` which will be 1 if there are multiple peaks for the same event and 0 otherwise.
    ### Args
    * `peaks`: list of peaks detected
    * `carray_i`: The wf
    * `mmean1`: mean of first 100 samples of background of carray_original
    * `stdev1`: stdev of first 100 samples of background of carray_original
    """
    # Extract array
    arr = carray_i[:,-1].copy()
    # Flag for multiple peaks for the same event
    F_double = 0
    # Check of multiple events 
    if len(peaks) > 1:
        peaks2 = np.copy(peaks)
        for v, v1 in zip(peaks2, peaks2[1:]):
            arrcalc = arr[v-deltav:].copy()
            arrcalc_blocks = np.lib.stride_tricks.sliding_window_view(arrcalc, blocksSize_dblEvent)
            meanblock = arrcalc_blocks.mean(axis=1)
            rowsL = np.where(np.logical_and(meanblock > mmean1 - stdev1,
                                            meanblock < mmean1 + stdev1))[0]
            if len(rowsL) > 0:
                firts_bkgblock_idx = rowsL[0] + v - deltav
                if firts_bkgblock_idx > v1:
                    peaks = peaks[peaks != v1]
                    F_double = 1
    return peaks, F_double

def f_copy_attrs(carray_original, carray_new):
    """
    This function copies the attributes of `carray_original` into `carray_new`, 
    iterating over the attributes of the first array, and manually sets them in the second.
    ### Args
    * `carray_original`: carray from which to copy the attributes
    * `carray_new`: carray into which to copy the attributes
    """
    # Get the attributes from the original carray
    original_attrs = carray_original.attrs
    # Copy the attributes to the new carray
    for name_attr in original_attrs._f_list():
        value_attr = original_attrs[name_attr]
        carray_new.attrs[name_attr] = value_attr
    carray_new.attrs['VERSION'] = f"3.{carray_original.attrs['VERSION']}"

def reset_time(carray, start_index, end_index, n_event=0, time_sts=0):
    """
    This function reset the time and date attributes associated to each wf extracted from the window [start_index, end_index]
    ### Args
    * `carray`: carray which need to the reset time and date attributes
    * `start_index`: index where starts the window of the wf
    * `end_index`: index where ends the window of the wf
    """
    def decompose_date(dt): 
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
           
    # Get attributes
    year = carray._v_attrs.Year
    month = carray._v_attrs.Month
    day = carray._v_attrs.Day
    hh = carray._v_attrs.HH
    mm = carray._v_attrs.mm
    ss = carray._v_attrs.ss
    usec = carray._v_attrs.usec
    tstart = carray._v_attrs.tstart
    # Calculate the time unit
    tdt = carray._v_attrs.Dec * 8e-9
    # Extract trigger
    curr_off = carray._v_attrs.CurrentOffset + 1
    trig_off = carray._v_attrs.TriggerOffset
    tstart_off = (len(carray)-curr_off)+trig_off if (curr_off > trig_off) else trig_off-curr_off
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
        year1, month1, day1, hh1, mm1, ss1, usec1 = decompose_date(date_time1)
    else:
        year1, month1, day1, hh1, mm1, ss1, usec1 = year, month, day, hh, mm, ss, usec
    return year1, month1, day1, hh1, mm1, ss1, usec1, tstart1, tend1

def get_endindex(carray_original, v, mmean1, stdev1, 
                 deltav=deltav, blocks_size=blocksSize_endindex, default_endindex=default_endindex):
    arr = carray_original[:, -1].copy()
    arrcalc = arr[v-deltav:].copy()
    arrcalc_blocks = np.lib.stride_tricks.sliding_window_view(arrcalc, blocks_size)
    meanblock = arrcalc_blocks.mean(axis=1)
    rowsL = np.where(np.logical_and(meanblock > mmean1 - stdev1,
                                    meanblock < mmean1 + stdev1))[0]
    if len(rowsL) > 0:
        end_index = rowsL[0] + v - deltav + blocks_size
    else:
        end_index = default_endindex
    return end_index

def dl02dl1(group_new, h5_out, carray_original, mmean1, stdev1, idx_new,
            deltac_sx=deltac_sx, deltac_dx=deltac_dx):
    """
    This function transform a wf of type `dl0` to a `dl1` to save memory space capturing
    only a window around each peak in the interval `[deltac_sx-peak, peak+deltac_dx]`
    ### Args
    * `group_new`: the group of h5 file out
    * `h5_out`: the h5 file out to save 
    * `carray_original`: the original carray saving the original wf
    * `mmean1`: mean of first 100 samples of background of carray_original
    * `stdev1`: stdev of first 100 samples of background of carray_original
    * `idx_new`: new wf idx to save its name 
    * `deltac_sx`: left range of the window around the peak
    * `deltac_dx`: right range of the window around the peak
    """
    atom = tb.Int16Atom()
    filters = tb.Filters(complevel=5, complib='zlib')
    # Extract the peaks list 
    peaks = get_peak_lists(carray_original, mmean1)
    # Get total number of peaks considering also double events
    n_peaks = len(peaks)
    # Filter from double events and the flag for multiple events
    peaks, isdouble = is_doubleevent(peaks, carray_original, mmean1, stdev1)
    if len(peaks) == 0:
        carray_name = 'wf_%s' % str(idx_new).zfill(6)
        arr = carray_original.read().copy()
        shape = (len(arr), 1)
        # window_array = carray_original.read()[start_index:end_index, -1]
        # window_array_np = window_array.astype(np.int16)*-1
        # compl2_carray = np.transpose(np.array([window_array_np]))
        # Creiamo un nuovo CArray con gli indici filtrati
        new_carray = h5_out.create_carray(group_new, carray_name, atom, shape, f'wf{idx_new}', filters=filters, obj=arr)
        # Copy the old attributes
        f_copy_attrs(carray_original, new_carray)
        # Add new attributes
        new_carray._v_attrs.wf_size     = -1
        new_carray._v_attrs.wf_start    = -1 
        new_carray._v_attrs.n_peaks     = 0
        new_carray._v_attrs.pk0_pos     = -1
        new_carray._v_attrs.pk0_tstart  = -1
        new_carray._v_attrs.peak_pos    = -1
        new_carray._v_attrs.peak_idx    = -1
        new_carray._v_attrs.mmean1      = mmean1
        new_carray._v_attrs.stdev1      = stdev1
        new_carray._v_attrs.isdouble    = isdouble
        new_carray._v_attrs.original_wf = carray_original._v_name
        # Increase the new indexes of wf
        idx_new += 1
    else:
        # Iterate over each peaks list for each wf_i
        for pk_idx, pk in enumerate(peaks):
            carray_name = 'wf_%s' % str(idx_new).zfill(6)
            # Calculate the indices to maintain
            start_index = max(pk - deltac_sx, 0)
            end_index = min(pk + deltac_dx, len(carray_original))
            end_index = get_endindex(carray_original, pk, mmean1, stdev1, default_endindex=end_index)
            compl2_carray = carray_original.read()[start_index:end_index]
            shape = (len(compl2_carray), 1)
            # window_array = carray_original.read()[start_index:end_index, -1]
            # window_array_np = window_array.astype(np.int16)*-1
            # compl2_carray = np.transpose(np.array([window_array_np]))
            # Creiamo un nuovo CArray con gli indici filtrati
            new_carray = h5_out.create_carray(group_new, carray_name, atom, shape, f'wf{idx_new}', filters=filters, obj=compl2_carray)
            # Copy the old attributes
            f_copy_attrs(carray_original, new_carray)
            # Add new attributes
            new_carray._v_attrs.wf_size     = end_index-start_index
            new_carray._v_attrs.wf_start    = start_index 
            new_carray._v_attrs.n_peaks     = n_peaks
            new_carray._v_attrs.pk0_pos     = peaks[0]
            new_carray._v_attrs.pk0_tstart  = carray_original._v_attrs.tstart
            new_carray._v_attrs.peak_pos    = pk
            new_carray._v_attrs.peak_idx    = pk_idx
            new_carray._v_attrs.mmean1      = mmean1
            new_carray._v_attrs.stdev1      = stdev1
            new_carray._v_attrs.isdouble    = isdouble
            new_carray._v_attrs.original_wf = carray_original._v_name
            # Date and time reset attrs
            new_carray._v_attrs.Year, new_carray._v_attrs.Month, new_carray._v_attrs.Day,                       \
                new_carray._v_attrs.HH, new_carray._v_attrs.mm, new_carray._v_attrs.ss,                         \
                new_carray._v_attrs.usec, new_carray._v_attrs.tstart1, new_carray._v_attrs.tend1 =              \
                reset_time(carray_original, start_index, end_index, time_sts=carray_original._v_attrs.TimeSts)
            # Increase the new indexes of wf
            idx_new += 1
    return idx_new


def main():
    parser = argparse.ArgumentParser(description='This routine converts an h5 file from type dl0 to dl1,'
                                                 'selecting from a waveform with more than 16k samples'
                                                 'to a smaller waveform in which the peak and the background'
                                                 'around it are reported.')    
    # Add the args
    parser.add_argument('source', type=str, help='Source file h5')
    parser.add_argument('dest', type=str, help='Dest file h5')
    # Parse arguments
    args = parser.parse_args()
    # Extract the parameters
    source = args.source
    dest = args.dest
    j = 0
    # Create the name of the new file of output of type dl1 
    fname_out = os.path.join(dest, os.path.basename(source).replace('.h5', '.dl1.h5'))
    print(fname_out)
    # Open the source file in read mode
    with tb.open_file(source, mode='r') as h5_in:
        group = h5_in.get_node("/waveforms")
        # Open the dest file in write mode
        with tb.open_file(fname_out, mode='w', title='dl1') as h5_out:
            # Create a new group where to save the new waveforms
            group1 = h5_out.create_group('/', 'waveforms', title='dl1')
            # Iterate over each wf_i, namely the carray_originals
            for carray_original_i in tqdm(group, total=group._g_getnchildren()):
                # Compute mean and std
                if carray_original_i._v_attrs.VERSION == "1.1":
                    shape_data = 1
                elif carray_original_i._v_attrs.VERSION == "2.0":
                    shape_data = 0
                mmean1 = carray_original_i[:100,shape_data].mean()
                stdev1 = carray_original_i[:100,shape_data].std()
                # 
                j = dl02dl1(group1, h5_out, carray_original_i, mmean1, stdev1, j)

if __name__ == "__main__":
    main()