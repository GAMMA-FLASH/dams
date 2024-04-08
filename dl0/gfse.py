import os
import sys
import socket
import struct
import math
from time import sleep

import argparse

from threading import Thread

import h5py

from waveform import Waveform, int_to_twos_comp
from crc32 import crc32_fill_table, crc32


def data_to_str(data):
    msg = ''
    for b in data:
        msg += "%02X" % b
    return "[%02d] 0x%s" % (len(data), msg)


def ds_to_wform(ds,rpID=None,runID=None,sessionID=None,configID=None):

    arr = ds[:]

    # trx is set using the current time since the std epoch
    wform = Waveform()

    if rpID:
        wform.rpID = rpID
    else:
        wform.rpID = ds.attrs['rp_id']

    if runID:
        wform.runID = runID
    else:
        wform.runID = ds.attrs['runid']

    if sessionID:
        wform.sessionID = sessionID
    else:
        wform.sessionID = ds.attrs['sessionID']

    if configID:
        wform.configID = configID
    else:
        wform.configID = ds.attrs['configID']

    wform.timeSts = ds.attrs['TimeSts']
    wform.ppsSliceNo = ds.attrs['PPSSliceNO']
    wform.year = ds.attrs['Year']
    wform.month = ds.attrs['Month']
    wform.day = ds.attrs['Day']
    wform.hh = ds.attrs['HH']
    wform.mm = ds.attrs['mm']
    wform.ss = ds.attrs['ss']
    wform.usec = ds.attrs['usec']

    # Time stamp is represented with a C/C++ timespec structure, hence
    # the Waveform creation time since std epoch in seconds is used
    # and converted into sec/nsec
    # NOTE: sec is set one second before the trx
    t = math.modf(wform.trx)
    wform.tstmp = (int(t[1]) - 1, round(t[0] * 1e9))

    wform.eql = ds.attrs['Eql']
    wform.dec = ds.attrs['Dec']

    # The buffer is already ordered
    wform.curr_off = arr.shape[0]-1
    wform.trig_off = 0

    wform.sample_no = arr.shape[0]

    wform.dt = float(wform.dec) * 8e-9

    # First/last sample time
    wform.tstart = float(wform.tstmp[0]) + float(wform.tstmp[1]) * 1e-9
    wform.tstop = wform.tstart + wform.dt * (wform.sample_no - 1)

    wform.data = []
    wform.trigt = []
    wform.sigt = []
    wform.sigr = []
    wform.sige = []

    # Convert numpy array to a tuple
    tpl = tuple(arr.reshape(1, -1)[0])

    # Reordering
    curr_off = wform.curr_off + 1
    if curr_off > wform.trig_off:
        pre1 = tpl[0:wform.trig_off]
        pre2 = tpl[wform.trig_off:curr_off]
        post = tpl[curr_off:]
        wform.data = ()
        for val in pre2 + post + pre1:
            wform.data += (int_to_twos_comp(val, 14),)
    else:
        pre = tpl[0:curr_off]
        post1 = tpl[curr_off:wform.trig_off]
        post2 = tpl[wform.trig_off:]
        wform.data = ()
        for val in post2 + pre + post1:
            wform.data += (int_to_twos_comp(val, 14),)

    return wform


START = 0x8D

# APID
CLASS_TC = 0x00
CLASS_TM = 0x80
CLASS_MASK = 0x80
SOURCE_MASK = 0x7F

# Sequence
GROUP_CONT = 0x0000
GROUP_FIRST = 0x4000
GROUP_LAST = 0x8000
GROUP_STAND_ALONE = 0xC000
GROUP_MASK = 0xC000
COUNT_MASK = 0x3FFF

U32_x_PACKET = 1020

SAMPLES_X_PACKET = 2*U32_x_PACKET

def create_header_packet(wform, srcid, npkt, crc_table):

    start = struct.pack("<B", START)
    apid = struct.pack("<B", CLASS_TM + srcid)
    seq = struct.pack("<H", GROUP_FIRST + npkt)

    runid = struct.pack("<H", wform.runID)
    size = struct.pack("<H", 44)

    #crc

    pkttype = struct.pack("<B", 0xA1) # 1
    subtype = struct.pack("<B", 0x01)
    sp0 = struct.pack("<B", 0x00)
    sp1 = struct.pack("<B", 0x00)

    sessionid = struct.pack("<H", wform.sessionID) # 2
    configid = struct.pack("<H", wform.configID)

    timests = struct.pack("<B", wform.timeSts) # 3
    ppssliceno = struct.pack("<B", wform.ppsSliceNo)
    year = struct.pack("<B", wform.year)
    month = struct.pack("<B", wform.month)

    day = struct.pack("<B", wform.day) # 4
    hh = struct.pack("<B", wform.hh)
    mm = struct.pack("<B", wform.mm)
    ss = struct.pack("<B", wform.ss)

    usec = struct.pack("<L", wform.usec) # 5

    ts0 = struct.pack("<L", wform.tstmp[0]) # 6

    ts1 = struct.pack("<L", wform.tstmp[1]) # 7

    sp2 = struct.pack("<B", wform.dec) #8

    eql = struct.pack("<B", wform.eql)

    dec = struct.pack("<H", wform.dec)

    curr_off =  struct.pack("<L", wform.curr_off) # 9

    trig_off = struct.pack("<L", wform.trig_off) # 10

    sno = struct.pack("<L", wform.sample_no) # 11

    data = pkttype
    data += subtype
    data += sp0
    data += sp1
    data += sessionid
    data += configid
    data += timests
    data += ppssliceno
    data += year
    data += month
    data += day
    data += hh
    data += mm
    data += ss
    data += usec
    data += ts0
    data += ts1
    data += eql
    data += sp2
    data += dec
    data += curr_off
    data += trig_off
    data += sno

    # Compute CRC
    crcval = 0xFFFFFFFF
    crcval = crc32(crcval, data, crc_table)

    crc = struct.pack("<L", crcval)

    pkt = start + apid + seq + runid + size + crc + data

    return pkt


def create_data_packet(wform, srcid, off, npkt, crc_table):

    nsmp = wform.sample_no - off
    if nsmp >= SAMPLES_X_PACKET:
        nsmp = SAMPLES_X_PACKET

    #print("off %d nsmp %d size %d" % (off, nsmp, nsmp/2+1))

    dataval = wform.data[off:(off+nsmp)]

    off += nsmp
    if off == wform.sample_no:
        grp = GROUP_LAST
    else:
        grp = GROUP_CONT

    start = struct.pack("<B", START)
    apid = struct.pack("<B", CLASS_TM + srcid)
    seq = struct.pack("<H", grp + npkt)

    runid = struct.pack("<H", wform.runID)
    size = struct.pack("<H", int(nsmp/2 + 1)*4)

    # crc

    pkttype = struct.pack("<B", 0xA1)
    subtype = struct.pack("<B", 0x02)
    sp0 = struct.pack("<B", 0x00)
    sp1 = struct.pack("<B", 0x00)

    data = pkttype + subtype + sp0 + sp1 + struct.pack("<%dH" % nsmp, *dataval)

    # Compute CRC
    crcval = 0xFFFFFFFF
    crcval = crc32(crcval, data, crc_table)

    crc = struct.pack("<L", crcval)

    pkt = start + apid + seq + runid + size + crc + data

    return off, pkt


def wform_to_packets(wform, srcid, npkt, crc_table):

    pkt = []

    # Create header packet
    hpkt = create_header_packet(wform, srcid, npkt, crc_table)
    npkt += 1
    pkt.append(hpkt)

    # Create data packets
    off = 0
    while off < wform.sample_no:
        off, dpkt = create_data_packet(wform, srcid, off, npkt, crc_table)
        npkt += 1
        pkt.append(dpkt)

    return npkt, pkt


def create_hk(state, flags, wform_count, crc_table):

    # Payload structure
    # [0] Type (uint8) 0x03
    # [1] SubType (uint8) 0x00
    # [2] State (uint8) 0x02 = SERVICE 0x03 ACQUISITION
    # [3] Flags (uint8) 0x80 = PPS_NOK 0x40 = GPS_NOK 0x20 = TRIG_ERR (no events)
    # [4] WaveCount (uint32)

    data = struct.pack("<BBBBI", 0x03, 0x01, state, flags, wform_count)

    # Compute CRC
    crc = 0xFFFFFFFF
    crc = crc32(crc, data, crc_table)

    # Create header
    tc_count = 0
    header = struct.pack("<BBHHHI", 0x8D, 0x00 + 0x0A, 0xC000 + tc_count, 0x0000, len(data), crc)

    return header + data


class SendThread(Thread):

    def __init__(self, conn, crc_table, dname, rpid, wform_dt, hk_rel_no, pkt_delay):

        Thread.__init__(self)
        self.conn = conn
        self.crc_table = crc_table
        self.dname = dname
        self.rpid = rpid
        self.wform_count = 0
        self.hk_count = 0
        self.wform_dt = wform_dt
        self.hk_rel_no = hk_rel_no
        self.pkt_delay = pkt_delay

        self.running = True

    def run(self):

        npkt = 0

        files = os.listdir(self.dname)

        for file in files:

            if self.running is True:

                fname = os.path.join(self.dname, file)
                print('INFO: Send: Open ', fname)
                try:
                    fin = h5py.File(fname, 'r')
                except:
                    print('ERROR: Send: File not valid')
                    continue

                group = fin['waveforms']
                for key in group:

                    if self.running is True:

                        ds = group[key]
                        wform = ds_to_wform(ds)

                        npkt, pkt = wform_to_packets(wform, self.rpid, npkt, self.crc_table)

                        for cur_pkt in pkt:
                            self.conn.send(cur_pkt)
                            sleep(self.pkt_delay)

                        self.wform_count += 1
                        self.hk_count += 1

                        if self.hk_count == self.hk_rel_no:
                            hk_pkt = create_hk(0x03, 0x80, self.wform_count, crc_table)
                            self.conn.send(hk_pkt)
                            sleep(self.pkt_delay)
                            self.hk_count = 0

                        sleep(self.wform_dt)

                    else:
                        break

            else:
                break

    def stop(self):
        self.running = False


DESCRIPTION = 'GammaFlash DAM server emulator v1.2.0'


if __name__ == '__main__':

    # ----------------------------------
    # Parse inputs
    # ----------------------------------

    # Configure input arguments
    parser = argparse.ArgumentParser(prog='gfse', description=DESCRIPTION)
    parser.add_argument('--addr', type=str, help='The Redpitaya IP address', required=True)
    parser.add_argument('--port', type=int, help='Server port', required=True)
    parser.add_argument('--indir', type=str, help='Input directory', required=True)
    parser.add_argument('--rpid', type=int, help='Redpitaya id', required=False)
    parser.add_argument('--wform-sec', type=float, help='Number of waveform per second', required=False, default=10.0)
    parser.add_argument('--hk-sec', type=float, help='Number of hk per second', required=False, default=0.2)
    parser.add_argument('--pkt-delay-sec', type=float, help='Delay between packets in seconds', required=False, default=0.00001)

    # Parse arguments and stop in case of help
    args = parser.parse_args(sys.argv[1:])

    print(args)

    wform_dt = 1/args.wform_sec

    print("INFO: Main: Waveform x sec %f (%f s)" % (args.wform_sec, wform_dt))

    hk_dt = 1/args.hk_sec
    hk_rel_no = round(hk_dt / wform_dt)

    print("INFO: Main: HK x sec %f (%f s, %d wform period)" % (args.hk_sec, hk_dt, hk_rel_no))

    print("INFO: Main: Packet delay %f s" % args.pkt_delay_sec)

    print(DESCRIPTION)

    # ----------------------------------
    # Open socket
    # ----------------------------------

    crc_table = crc32_fill_table(0x05D7B3A1)
    count = 0

    print("INFO: Main: Listen on ", args.port)

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the port
    server_address = (args.addr, int(args.port))
    sock.bind(server_address)

    # This should be a timeout on both accept and recv
    sock.settimeout(5)

    # Listen for incoming connections
    sock.listen(1)

    while True:

        # Wait for a connection
        print("INFO: Main: Waiting for connection")

        try:

            connection, client_address = sock.accept()
            connection.settimeout(5)

        except socket.timeout: #TimeoutError:
            continue

        except KeyboardInterrupt:
            break

        print("INFO: Main: Connection accepted from", client_address)

        # Receive the data
        send_thread = None
        while True:

            try:

                data = connection.recv(128)

                if data:
                    if data[13] == 0x04:
                        print("INFO: Main: Start acquisition")
                        send_thread = SendThread(connection, crc_table, args.indir, args.rpid, wform_dt, hk_rel_no, args.pkt_delay_sec)
                        send_thread.start()
                    elif data[13] == 0x05:
                        print("INFO: Main: Stop acquisition")
                        send_thread.stop()
                        send_thread.join()
                        send_thread = None
                        print("INFO: Main: Acquisition stopped")
                else:
                    print("INFO: Main: Connection closed")
                    break

            except socket.timeout: #TimeoutError:
                count += 1
                #send_hk(connection, crc_table, count)

            except KeyboardInterrupt:
                if send_thread:
                    send_thread.stop()
                    send_thread.join()
                    send_thread = None
                connection.close()
                break

            except:
                if send_thread:
                    send_thread.stop()
                    send_thread.join()
                    send_thread = None
                connection.close()
                break

    print('End')



