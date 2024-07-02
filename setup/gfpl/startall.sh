#!/bin/bash

GFCL=gfcl.py
PIDS=gfcl.pids

DL0_LOGS=$DAMS/logs/dl0

CONDA_ENV_NAME="gammaflash"

# Check if ODIR is defined
if [ -z "$ODIR" ]; then
    echo "ODIR not defined"
    exit 1
fi

# Check if DAMS is defined
if [ -z "$DAMS" ]; then
    echo "DAMS root not defined"
    exit 1
fi
mkdir -p $DL0_LOGS

cd $DAMS/dl0

# Check if gfcl.ini exists
if [ -e "gfcl.ini" ]; then
    echo "Using gfcl.ini: $(readlink -f gfcl.ini)"
else
    echo "gfcl.ini not defined"
    exit 1
fi
if [ "$(cat /etc/hostname)" = "gamma-flash.iasfbo.inaf.it" ]; then
    # Source the virtual environment (uncomment if needed)
    # source ~/venvs/gammaflash-influx/bin/activate
    PYTHON=python3.9
else
    source activate $CONDA_ENV_NAME
    PYTHON=python
fi

export PYTHONUNBUFFERED=yes
nohup $PYTHON $GFCL --addr 192.168.1.101 --port 1234 --outdir $ODIR/RPG101/35mV/ --wformno 1000 > $DL0_LOGS/gfcl_RP101.log &
nohup $PYTHON $GFCL --addr 192.168.1.102 --port 1234 --outdir $ODIR/RPG102/35mV/ --wformno 1000 > $DL0_LOGS/gfcl_RP102.log &
nohup $PYTHON $GFCL --addr 192.168.1.103 --port 1234 --outdir $ODIR/RPG103/35mV/ --wformno 1000 > $DL0_LOGS/gfcl_RP103.log &
nohup $PYTHON $GFCL --addr 192.168.1.104 --port 1234 --outdir $ODIR/RPG104/35mV/ --wformno 1000 > $DL0_LOGS/gfcl_RP104.log &
nohup $PYTHON $GFCL --addr 192.168.1.105 --port 1234 --outdir $ODIR/RPG105/35mV/ --wformno 1000 > $DL0_LOGS/gfcl_RP105.log &
nohup $PYTHON $GFCL --addr 192.168.1.106 --port 1234 --outdir $ODIR/RPG106/35mV/ --wformno 1000 > $DL0_LOGS/gfcl_RP106.log &
