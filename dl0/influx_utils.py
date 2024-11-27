
from enum import Enum


# ------------------------------------------------------------------ #
# Load influx DB modules                                             #
# ------------------------------------------------------------------ #

HAS_INFLUX_DB_COUNTS = False
HAS_INFLUX_DB_HK = False
try:
    from influxdb_client import InfluxDBClient, Point, WriteOptions,WritePrecision
    from influxdb_client.client.exceptions import InfluxDBError
    from influxdb_client.client.write_api import SYNCHRONOUS
    from influxdb_client.rest import ApiException
    HAS_INFLUX_DB_COUNTS = True
    HAS_INFLUX_DB_HK = True
except ImportError:
    print("Influx modules not found") 
    pass

# ------------------------------------------------------------------ #
# Global variables                                                   #
# ------------------------------------------------------------------ #

class TimestampOptions(Enum):
    RedPitaya = 'RP'  # Use tstart from the waveform
    MainComputer = 'MC'  # Sample the time from the main computer

INFLUX_DB_URL = None
INFLUX_DB_TOKEN = None
INFLUX_DB_ORG = None
INFLUX_DB_BUCKET = None
INFLUX_DB_BUCKET_HK = None

INFLUX_WF_TIMESTAMP : TimestampOptions = TimestampOptions.MainComputer
INFLUX_HK_TIMESTAMP : TimestampOptions = TimestampOptions.MainComputer


# ------------------------------------------------------------------ #
# Test Influx Connection                                             #
# ------------------------------------------------------------------ #

def _disable_influx():
    """Disable InfluxDB for the current session."""
    global HAS_INFLUX_DB_COUNTS, HAS_INFLUX_DB_HK
    HAS_INFLUX_DB_COUNTS = False
    HAS_INFLUX_DB_HK = False

def _test_influxdb_connection(url, token, org, on_failure):
    """Try Reach InfluxDB and disable influx on failure."""
    try:
        with InfluxDBClient(url=url, token=token, org=org) as client:
            buckets_api = client.buckets_api()
            buckets = buckets_api.find_buckets().buckets
            if buckets is None:
                raise InfluxDBError("Impossibile accedere ai bucket o accesso non autorizzato")
        print(f"Connection success")
        return True
    except (InfluxDBError, Exception) as e:
        print(f"Connection error while testing influx connection: {e}. Disabling for this session.")
        on_failure()  # Chiama la funzione per disabilitare InfluxDB
        return False

def parse_influx_params(cfg):
    """Interpreta la configurazione di InfluxDB dal file ini e prova la connessione."""
    global HAS_INFLUX_DB_COUNTS, HAS_INFLUX_DB_HK, INFLUX_DB_URL, INFLUX_DB_TOKEN
    global INFLUX_DB_ORG, INFLUX_DB_BUCKET, INFLUX_DB_BUCKET_HK, INFLUX_WF_TIMESTAMP, INFLUX_HK_TIMESTAMP

    if HAS_INFLUX_DB_HK or HAS_INFLUX_DB_COUNTS:
        # Controlla se InfluxDB è abilitato
        if cfg['INFLUXDB'].getboolean('Enable_Counts') or cfg['INFLUXDB'].getboolean('Enable_Hk'):
            print("INFO: Main: load influx DB connection parameters")
            INFLUX_DB_URL = cfg['INFLUXDB'].get("URL")
            INFLUX_DB_TOKEN = cfg['INFLUXDB'].get("Token")
            INFLUX_DB_ORG = cfg['INFLUXDB'].get("Org")

            # Abilita Counts
            if cfg['INFLUXDB'].getboolean('Enable_Counts'):
                print("Counts enabled")
                INFLUX_DB_BUCKET = cfg['INFLUXDB'].get("Bucket")
            else: 
                HAS_INFLUX_DB_COUNTS = False

            # Abilita Housekeeping
            if cfg['INFLUXDB'].getboolean('Enable_Hk'):
                print("Housekeeping enabled")
                INFLUX_DB_BUCKET_HK = cfg['INFLUXDB'].get("BucketHk")
            else:
                HAS_INFLUX_DB_HK = False

            # Timestamp
            try:
                INFLUX_WF_TIMESTAMP = TimestampOptions(cfg['INFLUXDB'].get("Timestamp_Wf"))
                print(f"Timestamp to load to influx set to: {INFLUX_WF_TIMESTAMP}")
                INFLUX_HK_TIMESTAMP = TimestampOptions(cfg['INFLUXDB'].get("Timestamp_Hk"))
                print(f"Timestamp to load to influx set to: {INFLUX_HK_TIMESTAMP}")
            except ValueError as e:
                print(f"WARNING: Cannot set 'TIMESTAMP' option: {e}. Using default value {TimestampOptions.MainComputer}")

            # Testa la connessione a InfluxDB
            if not _test_influxdb_connection(INFLUX_DB_URL, INFLUX_DB_TOKEN, INFLUX_DB_ORG, _disable_influx):
                print("InfluxDB disabilitato per questa sessione")
        else:
            _disable_influx()


