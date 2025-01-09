import os
import gc
import signal
import sys
import subprocess
import argparse
import struct
import socket
import threading
import time
import math
from threading import Thread
import multiprocessing
from multiprocessing import JoinableQueue, Process
from typing import List, Tuple, Type, Union
from queue import Queue, Full, Empty
from time import sleep
import tables as tb
import numpy as np
import configparser
import json
import zmq

from enum import Enum
import influx_utils as influx

from pathlib import Path

from packets import Waveform, Hk, Event
from crc32 import crc32_fill_table, crc32

# ------------------------------------------------------------------ #
# Load influx DB modules                                             #
# ------------------------------------------------------------------ #

try:
    from influxdb_client import InfluxDBClient, Point, WriteOptions,WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    from influxdb_client.rest import ApiException
    influx.HAS_INFLUX_DB_COUNTS = True
    influx.HAS_INFLUX_DB_HK = True
except ImportError:
    print("Influx modules not found") 
    pass

print("gc enabled: ", gc.isenabled())

stopped = multiprocessing.Event()  # Flag per indicare se il processo deve fermarsi
stop_save = multiprocessing.Event()  # Flag per indicare se il processo deve fermarsi
use_multiprocessing=False


def conditional_signal_handler(worker_class):
    if issubclass(worker_class, Process):
        signal.signal(signal.SIGINT, signal.SIG_IGN)

class BaseWorker:
    ...

class Recv(BaseWorker):

        def __init__(self, queue, sock, crc_table, rpid):

            super().__init__()
            self.pid if use_multiprocessing else threading.get_ident()
            self.queue = queue
            self.sock = sock
            self.rpId = rpid
            self.crc_table = crc_table
            self.data = bytes()
            self.pkt_count = 0
            self.wform_count = 0
            self.wform_seq_count = 0
            self.wform = None

        def run(self):
            conditional_signal_handler(self.__class__)
            while not stopped.is_set():
                try:
                    data = self.sock.recv(65536)
                except:
                    print("ERROR: Recv: Socket recv error")
                    continue
                try:
                    self.proc_bytes(data)
                except:
                    print("ERROR: Recv: Byte processing error %d" % len(data))
            print("Recv Exited")

        def proc_bytes(self, data):
            self.data += data
            off = 0
            while True:
                if len(self.data) - off > 0:
                    if self.data[off] == 0x8D:
                        if len(self.data) - off >= 12:
                            # [0] Start (uint8)
                            # [1] APID (uint8)
                            # [2] Sequence (uint16)
                            # [3] Run ID (uint16)
                            # [4] Size (uint16)
                            # [5] CRC (uint32)
                            header = struct.unpack("<BBHHHI", self.data[off:off + 12])
                            data_off = off + 12
                            if len(self.data) - data_off >= header[4]:
                                self.decode_pkt(header, self.data[data_off:data_off + header[4]])
                                off = data_off + header[4]
                            else:
                                self.data = self.data[off:]
                                break
                        else:
                            self.data = self.data[off:]
                            break
                    else:
                        off += 1
                else:
                    self.data = bytes()
                    break

        def decode_pkt(self, header, payload):
            # Check CRC
            # TODO: check CRC only on wform header/hk/events (??) on wform data only the sequence checking could be enough
            crc = 0xFFFFFFFF
            crc = crc32(crc, payload, self.crc_table)
            # Decode packets
            if crc == header[5]:
                if payload[0] == 0x01:  # Event
                    self.decode_event(header, payload)
                elif payload[0] == 0x03: # HK
                    self.decode_hk(header, payload)
                elif payload[0] == 0xA1: # Waveform
                    if payload[1] == 0x01: # Waveform header
                        self.decode_wform_header(header, payload)
                    else: # Waveform data
                        self.decode_wform_data(header, payload)
                else:
                    pass
            else:
                print("ERROR: Recv: Packet %02X %02X has wrong CRC" % (payload[0], payload[1]))

        def decode_wform_header(self, header, payload):
            self.wform_seq_count = header[2] & 0x3FFF
            self.wform = Waveform(rpID=header[1] & 0x7F, runID=header[3])

            self.wform.read_header(payload)

        def decode_wform_data(self, header, payload):
            seq_count = header[2] & 0x3FFF
            self.wform_seq_count += 1
            if self.wform_seq_count == seq_count:
                res = self.wform.read_data(payload)
                if res:
                    self.wform_count += 1
                    try:
                        self.queue.put(self.wform, timeout=5)
                    except Full:
                        print("ERROR: Recv: Queue is full")
                    except:
                        print("ERROR: Recv: Something went wrong in queue put")
            else:
                print("ERROR: Recv: Waveform packets sequence error")

        def decode_hk(self, header, payload):
            #print('Decode HK')
            hk = Hk(rpId = self.rpId)
            hk.read_data(payload)
            try:
                self.queue.put(hk, timeout=5)
            except Full:
                print("ERROR: Recv: Queue is full")
            except:
                print("ERROR: Recv: Something went wrong in queue put")

        def decode_event(self, header, payload):
            #print('Decode event')
            event = Event()
            event.read_data(payload)
            try:
                self.queue.put(event, timeout=5)
            except Full:
                print("ERROR: Recv: Queue is full")
            except:
                print("ERROR: Recv: Something went wrong in queue put")

class Save(BaseWorker):

        def __init__(self, queue, outdir, wformno, spectrum_cfg, dl0dl2_pipeline):
            super().__init__()
            self.pid if use_multiprocessing else threading.get_ident()
            self.queue = queue
            self.outdir = outdir
            self.dl2_dir = self.outdir.replace("DL0","DL2")
            self.wformno = wformno
            self.event_list: List[Event] = []
            self.save_event = False
            self.hk_list: List[Hk] = []
            self.save_hk = True
            self.wform_list: List[Waveform] = []
            self.wform_count = 0
            self._point = None
            self.spectrum_cfg = spectrum_cfg
            self.dl0dl2_pipeline = dl0dl2_pipeline
            self.output_path = None
            self.file_idx = 0
            self._configure_influxdb()
            self._configure_spectrum_an()
            
        def _configure_influxdb(self):
            # ------------------------------------------------------------------ #
            # Setup influx DB                                                    #
            # ------------------------------------------------------------------ #
    
            if influx.HAS_INFLUX_DB_COUNTS or influx.HAS_INFLUX_DB_HK :
                self.org = influx.INFLUX_DB_ORG
                self.client = InfluxDBClient(url=influx.INFLUX_DB_URL, token=influx.INFLUX_DB_TOKEN, org=self.org)
                if influx.HAS_INFLUX_DB_COUNTS : 
                    self.bucket = influx.INFLUX_DB_BUCKET
                    self.write_api = self.client.write_api(write_options=WriteOptions(batch_size=100,
                                                        flush_interval=1_000,
                                                        jitter_interval=2_000,
                                                        retry_interval=5_000,
                                                        max_retries=5,
                                                        max_retry_delay=30_000,
                                                        exponential_base=2))
                else:
                    self.bucket = None
                    self.write_api = None

                if influx.HAS_INFLUX_DB_HK :
                    self.write_api_hk = self.client.write_api(write_options=SYNCHRONOUS)
                    self.bucketHk = influx.INFLUX_DB_BUCKET_HK
                else:
                    self.bucketHk = None
                    self.write_api_hk = None
                print("SAVE-Influxdb configured")

            else:
                self.client = None
                self.write_api = None
                self.bucket = None
                self.org = None

        def _configure_spectrum_an(self):
            # ------------------------------------------------------------------ #
            # Setup spectrum analysis (DL2 via eventlistv4)                      #
            # ------------------------------------------------------------------ #
    
            if self.spectrum_cfg['Enable']:
                try:
                    expanded_process_out_value = os.path.expandvars(self.spectrum_cfg['ProcessOut'])
                    self.output_path = Path(expanded_process_out_value)
                    os.makedirs(self.output_path, exist_ok=True)
                    print("SAVE-spectrum analysis configured")
                except TypeError as e:
                    print("WARNING: DL2 output log folder not provided.")

        def _configure_rtadp(self):
            # ------------------------------------------------------------------ #
            # Setup rta-dp (DL1-DL2 production)                                  #
            # ------------------------------------------------------------------ #
            if self.dl0dl2_pipeline['Enable']:
                
                from ConfigurationManager import ConfigurationManager
                self.context = zmq.Context()
                cfgman= ConfigurationManager(dl0dl2_pipeline['json_data'])
                socketto_san=cfgman.get_configuration("DL0toDL1")["data_lp_socket"]
                print("----------->", socketto_san)
                self.socket_rtadp=self.context.socket(zmq.PUSH)
                try:
                    self.socket_rtadp.connect(socketto_san)
                    print("SAVE- Connected to : ", self.socket_rtadp)
                    print("SAVE- RTADP enabled")
                except Exception as e:
                    dl0dl2_pipeline['Enable'] = False
                    print(f"ERROR: cannot connect to rtadp. Reason: {e}")
            
            else: 
                self.socket_rtadp=None

        def _close_rtadp_connection(self):
            if dl0dl2_pipeline['Enable']:
                self.socket_rtadp.setsockopt(zmq.LINGER, 0)  # Imposta la chiusura immediata
                self.socket_rtadp.close()
                self.context.destroy()
                print("SAVE- RTADP connection closed")

        def run(self):
            self._configure_rtadp()
            conditional_signal_handler(self.__class__)
            # Create output directory (if needed)
            os.makedirs(self.outdir, exist_ok=True)

            while not stop_save.is_set() or self.queue.qsize() != 0:

                try:

                    packet = self.queue.get(timeout=5)

                except Empty:
                    if not stopped.is_set():
                        print('ERROR: Save: no data')
                    continue

                except:
                    print('ERROR: Save: something went wrong on queue get')
                    sleep(1)
                    continue
                
                # Signal that the object has been retrieved
                self.queue.task_done()
                
                if type(packet) is Event:
                    #print('Save event')
                    self.event_list.append(packet)
                elif type(packet) is Hk:
                    #print('Save HK')
                    packet.print()
                    if influx.HAS_INFLUX_DB_HK:
                        packet.influx(self.write_api_hk, self.bucketHk, self.org) 
                    self.hk_list.append(packet)
                else:

                    # ------------------------------------------------------------------ #
                    # Send data to influx DB                                             #
                    # ------------------------------------------------------------------ #

                    if influx.HAS_INFLUX_DB_COUNTS:
                    

                        if influx.INFLUX_WF_TIMESTAMP == influx.TimestampOptions.RedPitaya: 
                            time_ms = math.trunc((packet.tstart) * 1000) 
                        else: 
                            time_ms = math.trunc(time.time() * 1000) 
                        rpid = packet.rpID
                        print(f"INFO -- {rpid}")
                        if self._point is None:
                            self._point = Point("RPG%1d" % rpid).field("count", 1).time(time_ms, WritePrecision.MS)
                        else: 
                            self._point.time(time_ms, WritePrecision.MS)
                        
                        try:
                            self.write_api.write(self.bucket, self.org, record=self._point)
                        except ApiException as e :
                            print(f"API Exception: {e.status} - {e.reason}", file=sys.stderr)
                        except ConnectionError as e :
                            print(f"Connection Error: {e}", file=sys.stderr)
                        except Exception as e :
                            print(f"An unexpected error occurred: {e}", file=sys.stderr)




                    self.wform_list.append(packet)
                    self.wform_count += 1

                    if self.wform_count == self.wformno :

                        filename = self.dump_packets()
                                            
                        if self.spectrum_cfg['Enable']:
                            self.start_spectrum_an(filename=filename)
                        if self.dl0dl2_pipeline['Enable']:
                            self.send_rtadp_filename_spectrum_an(filename=filename)

                        self.flush_data()

                    else:
                        pass

                # if self.wform_count % 10 == 0:
                #     print(f"DEBUG - Queued packets: {self.queue.qsize()}, processed packets: {self.wform_count}")
                
            if influx.HAS_INFLUX_DB_COUNTS or influx.HAS_INFLUX_DB_HK:
                if influx.HAS_INFLUX_DB_COUNTS :
                    self.write_api.close()
                if influx.HAS_INFLUX_DB_HK : 
                    self.write_api_hk.close()
                self.client.close()
            
            if self.wform_count > 0:
                filename = self.dump_packets()
                                            
                if self.spectrum_cfg['Enable']:
                    self.start_spectrum_an(filename=filename)
                if self.dl0dl2_pipeline['Enable']:
                    self.send_rtadp_filename_spectrum_an(filename=filename)
            print('Dump queue')
            self._close_rtadp_connection()

        def start_spectrum_an(self, filename):
            inputfile = filename + '.h5'
            output_log = self.output_path.joinpath(f"{str(Path(filename).name)}.log")
            
            cmd=[
                f"source activate {self.spectrum_cfg['Venv']}",
                f"python {os.path.expandvars(self.spectrum_cfg['ProcessName'])} --outdir {self.dl2_dir} {self.spectrum_cfg['ProcessArgs']} --filename {inputfile} > {output_log} 2>&1"
            ]
            spectrum_cmd = " && ".join(cmd)
            print("DEBUG - process command: ", spectrum_cmd)

            subprocess.Popen(spectrum_cmd, shell=True)

        def send_rtadp_filename_spectrum_an(self, filename):
            inputfile = filename + '.h5'
            # output_log = self.output_path.joinpath(f"{str(Path(filename).name)}.log")
            
            # cmd=[
            #     f"source activate {self.spectrum_cfg['Venv']}",
            #     f"python {os.path.expandvars(self.spectrum_cfg['ProcessName'])} --outdir {self.dl2_dir} {self.spectrum_cfg['ProcessArgs']} --filename {inputfile} > {output_log} 2>&1"
            # ]
            # spectrum_cmd = " && ".join(cmd)
            # print("DEBUG - process command: ", spectrum_cmd)
            data = {"path_dl0_folder": os.path.dirname(inputfile), 
                    "path_dl1_folder": dl0dl2_pipeline['dl1_dir'], 
                    "path_dl2_folder": dl0dl2_pipeline['dl2_dir'], 
                    "filename":        os.path.basename(inputfile)}
            # Dump message
            message = json.dumps(data)
            self.socket_rtadp.send_string(message)
            print("DEBUG - data sent: ", data)
            # subprocess.Popen(spectrum_cmd, shell=True)s

        def dump_packets(self) -> str:
            # Note that the time needed to write the data is a function of the number of I/O ops
            # hence it is more efficient keeping the data into memory list and dump the lists in
            # one shot

            # print(len(self.event_list))
            # print(len(self.hk_list))
            # print(len(self.wform_list))

            # Create the file name using the rx time of the first waveform
            wf0 = self.wform_list[0]
            current_time = time.time()
            str1 = time.strftime("%Y-%m-%dT%H_%M_%S", time.gmtime(current_time))
            usec = round((current_time - int(current_time)) * 1e6)
            str2 = '%06d' % usec
            fname = '%s/wf_runId_%s_file_%s_configId_%s_%s.%s' % (self.outdir, str(wf0.runID).zfill(5), str(self.file_idx).zfill(10), str(wf0.configID).zfill(5), str1, str2)
            self.file_idx += 1
            print('Save file: ' + fname + '.h5')

            h5_out = tb.open_file(fname + '.h5', mode='w', title='dl0')

            wform_group = h5_out.create_group('/', 'waveforms', 'waveform information')

            atom = tb.Int16Atom()
            shape = (16384, 1)
            filters = tb.Filters(complevel=5, complib='zlib')

            for i, wf in enumerate(self.wform_list):
                arr = h5_out.create_carray(wform_group, 'wf_%s' % str(i).zfill(6), atom, shape, f'wf{i}', filters=filters)
                arr._v_attrs.VERSION = '2.0'
                arr._v_attrs.rp_id = wf.rpID
                arr._v_attrs.runid = wf.runID
                arr._v_attrs.sessionID = wf.sessionID
                arr._v_attrs.configID = wf.configID
                arr._v_attrs.TimeSts = wf.timeSts
                arr._v_attrs.PPSSliceNO = wf.ppsSliceNo
                arr._v_attrs.Year = wf.year
                arr._v_attrs.Month = wf.month
                arr._v_attrs.Day = wf.day
                arr._v_attrs.HH = wf.hh
                arr._v_attrs.mm = wf.mm
                arr._v_attrs.ss = wf.ss
                arr._v_attrs.usec = wf.usec
                arr._v_attrs.Eql = wf.eql
                arr._v_attrs.Dec = wf.dec
                arr._v_attrs.CurrentOffset = wf.curr_off
                arr._v_attrs.TriggerOffset = wf.trig_off
                arr._v_attrs.SampleNo = wf.sample_no
                arr._v_attrs.tstart = wf.tstart
                arr._v_attrs.tend = wf.tstop
                arr[:16384] = np.transpose(np.array([wf.sigr.astype(np.int16)]))[:16384]

            if self.save_hk:

                hk_group = h5_out.create_group('/', 'hk', 'hk information')

                shape = (1, 1)
                for i, hk in enumerate(self.hk_list):
                    arr = h5_out.create_carray(hk_group, 'hk_%s' % str(i).zfill(6), atom, shape, f'hk{i}', filters=filters)
                    arr._v_attrs.state = hk.state
                    arr._v_attrs.flags = hk.flags
                    arr._v_attrs.wform_count = hk.wform_count
                    if hk.timestamp_found():
                        arr._v_attrs.time = hk.compute_time()
                    arr[:] = 0

            h5_out.close()
            # Create the OK file
            # if self.dl0dl2_pipeline['Enable']:
            #     ok_out = open(fname + '.h5.ok', 'w')
            #     ok_out.close()

            return fname
        
        def flush_data(self):
            self.event_list = []
            self.hk_list = []
            self.wform_list = []
            self.wform_count = 0

def create_dynamic_classes(use_multiprocessing: bool) -> Tuple[Type[Union[Process, Thread]], Type[Union[Process, Thread]]]:
    """Crea due classi dinamiche che estendono `multiprocessing.Process` o `threading.Thread`."""
    base_class = Process if use_multiprocessing else Thread

    # Sostituzione della classe base
    Recv.__bases__ = (base_class,)
    Save.__bases__ = (base_class,)

    return Recv, Save

def start_acquisition(sock, crc_table):

    # Parameters
    #    Source: 0 = true, 1 = syntetic
    #  Constant: 0
    #    WaveNo: 0 = infinite, number of wfroms to be acquired
    # WaitUsecs: 0 = no wait, wait time before rearming in usecs 
    data = struct.pack("<BBBBII", 0xA0, 0x04, 0, 0, 0, 0)

    # Compute CRC
    crc = 0xFFFFFFFF
    crc = crc32(crc, data, crc_table)

    # Create header
    tc_count = 0
    header = struct.pack("<BBHHHI", 0x8D, 0x00 + 0x0A, 0xC000 + tc_count, 0x0000, len(data), crc)

    # Send
    sock.send(header + data)


def signal_handler(sig, frame):
    pid = os.getpid()  # Ottieni il PID del processo corrente
    print(f"[Main] Caught SIGINT in process {pid}, initiating shutdown...")
    stopped.set()  # Imposta il flag per fermare i processi


DESCRIPTION = 'GammaFlash client v2.0.1'


if __name__ == '__main__':
    # ----------------------------------
    # Parse inputs
    # ----------------------------------

    # Configure input arguments
    parser = argparse.ArgumentParser(prog='gfcl', description=DESCRIPTION)
    parser.add_argument('--rpid', type=str, help='The Redpitaya Identifier in the .cfg file', required=True)
    parser.add_argument('--addr', type=str, help='The Redpitaya IP address', required=True)
    parser.add_argument('--port', type=int, help='The Redpitaya port', required=True)
    parser.add_argument('--outdir', type=str, help='Output Directory', required=True)
    parser.add_argument('--wformno', type=int, help='Waveforms contained in HDF5 file', required=True)
    parser.add_argument('--multiprocessing', action='store_true', help='if present, enable multiprocessing')

    # Parse arguments and stop in case of help
    args = parser.parse_args(sys.argv[1:])

    print(DESCRIPTION)

    if not influx.HAS_INFLUX_DB_HK or not influx.HAS_INFLUX_DB_COUNTS:
        print("INFO: Main: No influx DB module found")

    # ----------------------------------
    # Load configuration
    # ----------------------------------
    cfg = configparser.ConfigParser()
    cfg.read('gfcl.ini')
    influx.parse_influx_params(cfg)
    
    spectrum_cfg={
            'Enable' : cfg['SPECTRUM_AN'].getboolean('Enable'),
            'Venv'  : cfg['SPECTRUM_AN'].get('Venv'),
            'ProcessName' : cfg['SPECTRUM_AN'].get('ProcessName'),
            'ProcessArgs' : cfg['SPECTRUM_AN'].get('ProcessArgs'),
            'ProcessOut' : cfg['SPECTRUM_AN'].get('ProcessOut')
            }

    dl0dl2_pipeline={
            'Enable' : cfg['DL0DL2_PIPE'].getboolean('Enable'), 
            'json_data': os.getenv(cfg['DL0DL2_PIPE'].get('RTADPCONFIG_VAR')),
            'dl1_dir': os.getenv(cfg['DL0DL2_PIPE'].get('RTADPDL1OUT_VAR')),
            'dl2_dir': os.getenv(cfg['DL0DL2_PIPE'].get('RTADPDL2OUT_VAR')),
            }

    # ----------------------------------
    # Open socket
    # ----------------------------------

    print("INFO: Main: Connecting to ", args.addr, args.port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    try:
        sock.connect((args.addr, args.port))
    except:
        print("ERROR: Main: Socket connection timed out")
        quit()

    sock.settimeout(5)

    # ----------------------------------
    # Start client
    # ----------------------------------
    
    chosen_queue_type : Union[JoinableQueue, Queue]= None

    if args.multiprocessing : 
        use_multiprocessing = True
        chosen_queue_type = JoinableQueue
    else: 
        chosen_queue_type = Queue
        
    queue = chosen_queue_type(args.wformno)

    Dyn_Recv , Dyn_Save = create_dynamic_classes(use_multiprocessing=use_multiprocessing)

    
    print(f"Chosen queue type: {chosen_queue_type.__name__}")
    print(f"Base class of RecvClass: {Dyn_Recv.__bases__[0].__name__}")
    print(f"Base class of SaveClass: {Dyn_Save.__bases__[0].__name__}")

    # Adapt signal handling to multiprocessing

    signal.signal(signal.SIGINT, signal_handler)

    save_thread : Union[Process, Thread] = Dyn_Save(queue, args.outdir, args.wformno, spectrum_cfg, dl0dl2_pipeline)
    save_thread.start()

    sleep(1)

    # Create CRC table
    crc_table = crc32_fill_table(0x05D7B3A1)

    recv_thread : Union[Process, Thread] = Dyn_Recv( queue, sock, crc_table, args.rpid)
    recv_thread.start()

    # ----------------------------------
    # Start acquisition
    # ----------------------------------

    sleep(5)

    print("INFO: Main: Start data acquistion")

    start_acquisition(sock, crc_table)

    # ----------------------------------
    # Monitor loop
    # ----------------------------------
    while not stopped.is_set():
        sleep(5)

    # ----------------------------------
    # Ordered shutdown
    # ----------------------------------

    print('INFO: Main: Stop recv thread')
    recv_thread.join()

    print('INFO: Main: Wait till data saving is complete')
    queue.join()
    stop_save.set()
    print('INFO: Main: Stop save thread')
    save_thread.join()

    print('End')
