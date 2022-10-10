import sys
import time
import socket
import struct
import argparse
from threading import Thread
from Logger import Logger
from waveform import Waveform
from hdf5create import Hdf5Create
from crc32 import crc32_fill_table, crc32
from multiprocessing import Process, Queue


class RecvThread(Thread):
    
    def __init__(self, sock, rep_id):

        Thread.__init__(self)
        self.sock = sock
        self.rep_id = rep_id
        self.data = bytes()
        self.running = True
        self.tmtowf = TmtoWF(rep_id)

    def run(self):
        while self.running is True:
            try:
                data = self.sock.recv(65536)
            except:
                print("Socket recv error")
                continue
            try:
                self.parse(data)
            except:
                print("Parse error")

    def stop(self):
        self.running = False

    def parse(self,data):
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
                            #self.rxTmSig.emit(header, self.data[data_off:data_off + header[4]])
                            self.tmtowf.tmtowf_nogui(header, self.data[data_off:data_off + header[4]])
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

class TmtoWF():

    def __init__(self, repId) -> None:


        loggerConfig = Logger()
        loggerConfig.set_logger()
        
        self.logger = Logger().getLogger(__name__)

        self.hdf5create = Hdf5Create()
        self.wformTotCount = 0
        self.repId = repId

        self.q = Queue()
        self.p = Process(target=Hdf5Create.f, args=(self.hdf5create, self.q))
        self.p.start()

    def tmtowf_nogui(self, header, data):
        if data[0] == 0xA1: # Waveform
            if data[1] == 0x01: # Waveform header
                #self.tmToLog(header, data)
                self.tmToWformInit(header, data)
            else: # Waveform data
                self.tmToWformAdd(header, data)
        else:
            pass
            #self.tmToLog(header, data)

    def tmToWformInit(self, header, data):
        self.wformSeqCount = header[2] & 0x3FFF
        self.wform = Waveform(runID=header[3])
        self.wform.set_rpID(self.repId)
        self.wform.read_header(data)

    def tmToWformAdd(self, header, data):
        seqCount = header[2] & 0x3FFF
        self.wformSeqCount += 1
        if self.wformSeqCount == seqCount:
            res = self.wform.read_data(data)
            if res:
                #self.wform.print()
                self.wformTotCount += 1
                print("Complete waveform acquired [%d]" % self.wformTotCount) #waveform totale acquisita
                #self.logger.warning(f"Complete waveform acquired {self.wformTotCount}")
                self.q.put(self.wform)

        else:
            print("Sequence error: cur %6d exp %6d" % (seqCount, self.wformSeqCount))

def start_acquisition(sock, crc_table):
    # Create data section
    # source detector == 0, simulator == 1
    source = 0
    # Waveform number infinite = 0
    waveform_no = 0
    # wait us
    wait_us = 0

    data = struct.pack("<BBBBII", 0xA0, 0x04, source, 0, waveform_no, wait_us)

    # Compute CRC
    crc = 0xFFFFFFFF
    crc = crc32(crc, data, crc_table)

    # Create header
    tc_count = 0
    header = struct.pack("<BBHHHI", 0x8D, 0x00 + 0x0A, 0xC000 + tc_count, 0x0000, len(data), crc)

    # Send
    sock.send(header + data)

if __name__ == '__main__':
    
    #Parse inputs
    parser = argparse.ArgumentParser()
    parser.add_argument('--rp_ip', type=str, help='The Redpitaya IP address', required=True)
    parser.add_argument('--rp_port', type=int, help='The Redpitaya port', required=True)
    parser.add_argument('--rp_id', type=int, help='The Redpitaya id', required=True)
    
    args = parser.parse_args()
    
    #Open the socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    try:
        sock.connect((args.rp_ip, args.rp_port))
    except:
        print("ERROR: Socket connection timed out")
        quit()
        
    sock.settimeout(5)

    #Start receiving thread

    recv_thread = RecvThread(sock, args.rp_id)

    recv_thread.start()

    crc_table = crc32_fill_table(0x05D7B3A1)

    time.sleep(10)
    
    #Send starting command
    print("start acquisition")
    start_acquisition(sock, crc_table)

    while True:
        time.sleep(5)