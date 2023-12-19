#!/bin/bash

GFCL=gfcl.py
PIDS=gfcl.pids

#change to script directory:
cd "$(dirname "$0")"

# Check if ODIR is defined
if [ -z "$ODIR" ]; then
    echo "ODIR not defined"
    exit 1
fi

# Check if gfcl.ini exists
if [ -e "gfcl.ini" ]; then
    echo "Using gfcl.ini: $(readlink -f gfcl.ini)"
else
    echo "gfcl.ini not defined"
    exit 1
fi
if [ "$(hostname)" = "gamma-flash.iasfbo.inaf.it" ]; then
    # Source the virtual environment (uncomment if needed)
    # source ~/venvs/gammaflash-influx/bin/activate
    PYTHON=python3.9
else
    PYTHON=python
fi
nohup $PYTHON $GFCL --addr 192.168.1.101 --port 1234 --outdir $ODIR/RPG101/35mV/ --wformno 1000 > gfcl_RP101.log &
nohup $PYTHON $GFCL --addr 192.168.1.102 --port 1234 --outdir $ODIR/RPG102/35mV/ --wformno 1000 > gfcl_RP102.log &
nohup $PYTHON $GFCL --addr 192.168.1.103 --port 1234 --outdir $ODIR/RPG103/35mV/ --wformno 1000 > gfcl_RP103.log &
nohup $PYTHON $GFCL --addr 192.168.1.104 --port 1234 --outdir $ODIR/RPG104/35mV/ --wformno 1000 > gfcl_RP104.log &
nohup $PYTHON $GFCL --addr 192.168.1.105 --port 1234 --outdir $ODIR/RPG105/35mV/ --wformno 1000 > gfcl_RP105.log &
nohup $PYTHON $GFCL --addr 192.168.1.106 --port 1234 --outdir $ODIR/RPG106/35mV/ --wformno 1000 > gfcl_RP106.log &

sleep 1 

pgrep -f "$GFCL" > $PIDS

cat $PIDS

# nohup python gfcl.py --addr 192.168.1.101 --port 1234 --outdir $ODIR/RPG101/35mV/ --wformno 1000 > gfcl_RP101.log &
# nohup python gfcl.py --addr 192.168.1.102 --port 1234 --outdir $ODIR/RPG102/35mV/ --wformno 1000 > gfcl_RP102.log &
# nohup python gfcl.py --addr 192.168.1.103 --port 1234 --outdir $ODIR/RPG103/35mV/ --wformno 1000 > gfcl_RP103.log &
# nohup python gfcl.py --addr 192.168.1.104 --port 1234 --outdir $ODIR/RPG104/35mV/ --wformno 1000 > gfcl_RP104.log &
# nohup python gfcl.py --addr 192.168.1.105 --port 1234 --outdir $ODIR/RPG105/35mV/ --wformno 1000 > gfcl_RP105.log &
# nohup python gfcl.py --addr 192.168.1.106 --port 1234 --outdir $ODIR/RPG106/35mV/ --wformno 1000 > gfcl_RP106.log &