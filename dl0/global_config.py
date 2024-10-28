import gc
from enum import Enum
import multiprocessing

print("gc enabled: ", gc.isenabled())
# ------------------------------------------------------------------ #
# Load influx DB modules                                             #
# ------------------------------------------------------------------ #

HAS_INFLUX_DB_COUNTS = False
HAS_INFLUX_DB_HK = False
try:
    from influxdb_client import InfluxDBClient, Point, WriteOptions,WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    from influxdb_client.rest import ApiException
    HAS_INFLUX_DB_COUNTS = True
    HAS_INFLUX_DB_HK = True
except ImportError:
    print("Influx modules not found") 
    pass

class TimestampOptions(Enum):
    RedPitaya = 'RP'  # Use tstart from the waveform
    MainComputer = 'MC'  # Sample the time from the main computer

# ------------------------------------------------------------------ #
# Global variables                                                   #
# ------------------------------------------------------------------ #
INFLUX_DB_URL = None
INFLUX_DB_TOKEN = None
INFLUX_DB_ORG = None
INFLUX_DB_BUCKET = None
INFLUX_DB_BUCKET_HK = None

INFLUX_WF_TIMESTAMP : TimestampOptions = TimestampOptions.MainComputer
INFLUX_HK_TIMESTAMP : TimestampOptions = TimestampOptions.MainComputer

# ------------------------------------------------------------------ #
# Global variables                                                   #
# ------------------------------------------------------------------ #

