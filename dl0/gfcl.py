import os
import sys
import argparse
import struct
import socket
import time
import math
from threading import Thread
from queue import Queue, Full, Empty
from time import sleep
import tables as tb
import numpy as np
import configparser

from waveform import Waveform
from crc32 import crc32_fill_table, crc32

# ------------------------------------------------------------------ #
# Load influx DB modules                                             #
# ------------------------------------------------------------------ #
HAS_INFLUX_DB = False
try:
    from influxdb_client import InfluxDBClient, Point, WriteOptions,WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    HAS_INFLUX_DB = True
except ImportError:
    pass

# ------------------------------------------------------------------ #
# Global variables                                                   #
# ------------------------------------------------------------------ #
INFLUX_DB_URL = None
INFLUX_DB_TOKEN = None
INFLUX_DB_ORG = None
INFLUX_DB_BUCKET = None


class Event:
    def __init__(self,trx=None):

        # Receive time in secs past January 1, 1970, 00:00:00 (UTC)
        if trx is None:
            self.trx = time.time()
        else:
            self.trx = trx

    def read_data(self, raw):
        pass


class Hk:
    def __init__(self,trx=None):

        # Receive time in secs past January 1, 1970, 00:00:00 (UTC)
        if trx is None:
            self.trx = time.time()
        else:
            self.trx = trx

        self.state = 0
        self.flags = 0
        self.wform_count = 0

    def read_data(self,raw):
        # Payload structure
        # [0] Type (uint8)
        # [1] SubType (uint8)
        # [2] State (uint8) 0x02 = SERVICE 0x03 ACQUISITION
        # [3] Flags (uint8) 0x80 = PPS_NOK 0x40 = GPS_NOK 0x20 = TRIG_ERR (no events)
        # [4] WaveCount (uint32)
        # Add temperature??
        self.state = struct.unpack('<B', raw[2:3])[0]
        self.flags = struct.unpack('<B', raw[3:4])[0]
        self.wform_count = struct.unpack('<I', raw[4:])[0]


class RecvThread(Thread):

    def __init__(self, queue, sock, crc_table):
        Thread.__init__(self)
        self.queue = queue
        self.sock = sock
        self.crc_table = crc_table
        self.data = bytes()
        self.pkt_count = 0
        self.wform_count = 0
        self.wform_seq_count = 0
        self.wform = None
        self.running = True

    def run(self):
        while self.running is True:
            try:
                data = self.sock.recv(65536)
            except:
                print("ERROR: Recv: Socket recv error")
                continue
            try:
                self.proc_bytes(data)
            except:
                print("ERROR: Recv: Byte processing error %d" % len(data))

    def stop(self):
        self.running = False

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
        self.wform = Waveform(rpID=header[1], runID=header[3])
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
        hk = Hk()
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


class SaveThread(Thread):

    def __init__(self, queue, outdir, wformno):
        Thread.__init__(self)
        self.queue = queue
        self.outdir = outdir
        self.wformno = wformno
        self.event_list = []
        self.save_event = False
        self.hk_list = []
        self.save_hk = True
        self.wform_list = []
        self.wform_count = 0
        self.running = True

        # ------------------------------------------------------------------ #
        # Setup influx DB                                                    #
        # ------------------------------------------------------------------ #

        if HAS_INFLUX_DB:

            #url = "172.17.0.2:8086"
            #token = "uQmtmZMYQb-iiyB66CuO91eDUemEc2-l-eWza8hq6ehKoM4TVNj_Y0vIGKgrDUYi4XX9qQXEiPD5kNTYRK_ITQ=="
            #org = "GAMMA-FLASH"
            #bucket = "RP-DATA"

            self.client = InfluxDBClient(url=INFLUX_DB_URL, token=INFLUX_DB_TOKEN, org=INFLUX_DB_ORG)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.bucket = INFLUX_DB_BUCKET
            self.org = INFLUX_DB_ORG

        else:
            self.client = None
            self.write_api = None
            self.bucket = None
            self.org = None

    def run(self):

        # Create output directory (if needed)
        os.makedirs(self.outdir, exist_ok=True)

        while self.running is True:

            try:

                packet = self.queue.get(timeout=5)

            except Empty:
                if self.running is True:
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
                self.hk_list.append(packet)
            else:

                # ------------------------------------------------------------------ #
                # Send data to influx DB                                             #
                # ------------------------------------------------------------------ #

                if HAS_INFLUX_DB:
                    time_ms = math.trunc(packet.tstart * 1000)
                    self.write_api.write(self.bucket, self.org, Point("RPG%1d" % packet.rpID).field("count", 1).time(time_ms, WritePrecision.MS))

                #print('Save wform')
                self.wform_list.append(packet)
                self.wform_count += 1

                if self.wform_count == self.wformno:

                    # Note that the time needed to write the data is a function of the number of I/O ops
                    # hence it is more efficient keeping the data into memory list and dump the lists in
                    # one shot

                    # print(len(self.event_list))
                    # print(len(self.hk_list))
                    # print(len(self.wform_list))

                    # Create the file name using the rx time of the first waveform
                    wf0 = self.wform_list[0]
                    ts = time.gmtime(wf0.trx)
                    str1 = time.strftime("%Y-%m-%dT%H_%M_%S", ts)
                    sns = math.modf(wf0.trx)
                    usec = round(sns[0] * 1e6)
                    str2 = '%06d' % usec
                    fname = '%s/wf_runId_%s_configId_%s_%s.%s' % (self.outdir, str(wf0.runID).zfill(5), str(wf0.configID).zfill(5), str1, str2)

                    print('Open file: ' + fname + '.h5')

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
                        arr[:16384] = np.transpose(np.array([wf.sigr.astype(np.int16)*-1]))[:16384]

                    if self.save_hk:

                        hk_group = h5_out.create_group('/', 'hk', 'hk information')

                        shape = (1, 1)
                        for i, hk in enumerate(self.hk_list):
                            arr = h5_out.create_carray(hk_group, 'hk_%s' % str(i).zfill(6), atom, shape, f'hk{i}', filters=filters)
                            arr._v_attrs.state = hk.state
                            arr._v_attrs.flags = hk.flags
                            arr._v_attrs.wform_count = hk.wform_count
                            arr[:] = 0

                    h5_out.close()

                    print('Close file')

                    # Create the OK file
                    ok_out = open(fname + '.h5.ok', 'w')
                    ok_out.close()

                    self.event_list = []
                    self.hk_list = []
                    self.wform_list = []

                    self.wform_count = 0

                else:
                    pass

        print('Dump queue')

    def stop(self):
        self.running = False


def start_acqusition(sock, crc_table):

    data = struct.pack("<BBBBII", 0xA0, 0x04, 0, 0, 0, 0)

    # Compute CRC
    crc = 0xFFFFFFFF
    crc = crc32(crc, data, crc_table)

    # Create header
    tc_count = 0
    header = struct.pack("<BBHHHI", 0x8D, 0x00 + 0x0A, 0xC000 + tc_count, 0x0000, len(data), crc)

    # Send
    sock.send(header + data)


DESCRIPTION = 'GammaFlash client v2.0.1'


if __name__ == '__main__':

    # ----------------------------------
    # Parse inputs
    # ----------------------------------

    # Configure input arguments
    parser = argparse.ArgumentParser(prog='gfcl', description=DESCRIPTION)
    parser.add_argument('--addr', type=str, help='The Redpitaya IP address', required=True)
    parser.add_argument('--port', type=int, help='The Redpitaya port', required=True)
    parser.add_argument('--outdir', type=str, help='Output Directory', required=True)
    parser.add_argument('--wformno', type=int, help='Waveforms contained in HDF5 file', required=True)

    # Parse arguments and stop in case of help
    args = parser.parse_args(sys.argv[1:])

    print(DESCRIPTION)

    if not HAS_INFLUX_DB:
        print("INFO: Main: No influx DB module found")

    # ----------------------------------
    # Load configuration
    # ----------------------------------
    cfg = configparser.ConfigParser()
    cfg.read('gfcl.ini')
    if HAS_INFLUX_DB:
        if cfg['INFLUXDB'].getboolean('Enable'):
            print("INFO: Main: load influx DB connection pramaters")
            INFLUX_DB_URL = cfg['INFLUXDB'].get("URL")
            INFLUX_DB_TOKEN = cfg['INFLUXDB'].get("Token")
            INFLUX_DB_ORG = cfg['INFLUXDB'].get("Org")
            INFLUX_DB_BUCKET = cfg['INFLUXDB'].get("Bucket")
        else:
            HAS_INFLUX_DB = False

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

    queue = Queue()

    save_thread = SaveThread(queue, args.outdir, args.wformno)
    save_thread.start()

    sleep(1)

    # Create CRC table
    crc_table = crc32_fill_table(0x05D7B3A1)

    recv_thread = RecvThread(queue, sock, crc_table)
    recv_thread.start()

    # ----------------------------------
    # Start acquisition
    # ----------------------------------

    sleep(5)

    print("INFO: Main: Start data acquistion")

    start_acqusition(sock, crc_table)

    # ----------------------------------
    # Monitor loop
    # ----------------------------------

    while True:
        try:
            print("INFO: Main: Running ")
            sleep(5)
        except KeyboardInterrupt:
            break

    # ----------------------------------
    # Ordered shutdown
    # ----------------------------------

    print('INFO: Main: Stop recv thread')
    recv_thread.stop()
    recv_thread.join()

    print('INFO: Main: Wait till data saving is complete')
    queue.join()

    print('INFO: Main: Stop save thread')
    save_thread.stop()
    save_thread.join()

    print('End')






