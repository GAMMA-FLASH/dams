import math
import struct
import sys
import time
import global_config

try:
    from influxdb_client import Point, WritePrecision
    from influxdb_client.rest import ApiException
except ImportError:
    print("Influx modules not found") 
    pass



class Hk:
    def __init__(self, rpId=None):
        self.rpId = rpId
        # Receive time in secs past January 1, 1970, 00:00:00 (UTC)
        
        self.trx = time.time() #save instantiation time
        self.tstmp = None

        self.state = 0
        self.flags = 0
        self.wform_count = 0
        self._point = None

    def read_data(self,raw):
        # Payload structure
        # [0] Type (uint8)
        # [1] SubType (uint8)
        # [2] State (uint8) 0x02 = SERVICE 0x03 ACQUISITION
        # [3] Flags (uint8) 0x80 = PPS_NOK 0x40 = GPS_NOK 0x20 = TRIG_ERR (no events)
        # [4] WaveCount (uint32)
        # [8] Timestamp (2*uint32)
        # Add temperature??
        self.state = struct.unpack('<B', raw[2:3])[0]
        self.flags = struct.unpack('<B', raw[3:4])[0]
        self.wform_count = struct.unpack('<I', raw[4:8])[0]
        if len(raw) > 8:  ##for backward compatibility

            self.tstmp = struct.unpack("<LL", raw[8:])  # timespec sec.nsec
        
    def compute_time(self):
        return float(self.tstmp[0]) + float(self.tstmp[1]) * 1e-9
    
    def timestamp_found(self):
        return True if self.tstmp is not None else False

    def print(self):
        #print("    State: %02X" % self.state)
        #print("    Flags: %02X" % self.flags)
        #print("Wform no.: %d" % self.wform_count)
        msg = ''
        if self.tstmp is None:
            msg = Hk.trx_to_str(self.trx)
        else : 
            msg = Hk.tmstp_to_str(self.tstmp)
        msg += ' '
        if self.state == 0x02:
            msg += 'SRV'
        elif self.state == 0x03:
            msg += 'ACQ'
        else:
            msg += 'UNK'
        if self.flags & 0x80:
            msg += ' P'
        else:
            msg += ' _'
        if self.flags & 0x40:
            msg += 'Gu'
        else:
            msg += '__'
        if self.flags & 0x20:
            msg += 'Go'
        else:
            msg += '__'
        if self.flags & 0x10:
            msg += 'Gt'
        else:
            msg += '__'
        if self.flags & 0x01:
            msg += 'T'
        else:
            msg += '_'
        msg += ' %5d' % self.wform_count
        print(msg)

    @staticmethod
    def trx_to_str(trx):
        ts = time.gmtime(trx)
        str1 = time.strftime("%Y%m%d-%H:%M:%S", ts)
        sns = math.modf(trx)
        usec = round(sns[0] * 1e6)
        str2 = '%06d' % usec
        return "[Hk - MC time]" + str1 + "." + str2

    @staticmethod
    def tmstp_to_str(tmstp):
        ts = time.gmtime(tmstp[0])
        str1 = time.strftime("%Y%m%d-%H:%M:%S", ts)
        nsec = tmstp[1]
        str2 = '%06d' % nsec
        return "[Hk - RP time]" + str1 + "." + str2

    def influx(self, write_api=None, bucket = None, org = None):
        #print("    State: %02X" % self.state)
        #print("    Flags: %02X" % self.flags)
        #print("Wform no.: %d" % self.wform_count)

        measurement_name = f"RPG{self.rpId}"

        pps = 1 if self.flags & 0x80 else 0
        gps_no_uart = 1 if self.flags & 0x40 else 0
        gps_overtime = 1 if self.flags & 0x20 else 0
        gps_invalid_time = 1 if self.flags & 0x10 else 0
        err = 1 if self.flags & 0x01 else 0

        if global_config.INFLUX_HK_TIMESTAMP == global_config.TimestampOptions.MainComputer:
            timepoint_influx = math.trunc(self.trx * 1000)
            write_precision_influx=WritePrecision.MS
        else:
            # print("inserintg data")

            timepoint_influx = int(self.tstmp[0]*1e9+self.tstmp[1])
            write_precision_influx=WritePrecision.NS
    
        self._point = (
            Point(measurement_name)
            .field("state", self.state)
            .field("PPS_NOK", pps)
            .field("GPS_UART_NOK", gps_no_uart)
            .field("GPS_OVERTIME", gps_overtime)
            .field("GPS_TIME_NOK", gps_invalid_time)
            .field("ERR", err)
            .field("count", self.wform_count)
            .time(timepoint_influx, write_precision_influx)
        )
        
        try:
            write_api.write(bucket=bucket, org=org, record=self._point)        
        except ApiException as e :
            print(f"API Exception: {e.status} - {e.reason}", file=sys.stderr)
        except ConnectionError as e :
            print(f"Connection Error: {e}", file=sys.stderr)
        except Exception as e :
            print(f"An unexpected error occurred: {e}", file=sys.stderr)