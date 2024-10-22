#!/bin/bash

PIDS=gfcl.pids

CONDA_ENV_NAME="gammaflash"
# Change to script directory:
GAMMAFLASH_DAMS_PATH=$(dirname $(dirname $(dirname "$(realpath "$0")")))
cd $GAMMAFLASH_DAMS_PATH/dl0

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

GFCL=${GFCL:-"$DAMS/dl0/gfcl.py"}
echo "Using Client Script: ${GFCL}"

# Check if gfcl.ini exists
if [ -e "gfcl.ini" ]; then
    echo "Using gfcl.ini: $(readlink -f gfcl.ini)"
else
    echo "gfcl.ini not defined"
    exit 1
fi

IP_ADDRESS=$1

if [ "$(cat /etc/hostname)" = "gamma-flash.iasfbo.inaf.it" ]; then
    # Source the virtual environment (uncomment if needed)
    # source ~/venvs/gammaflash-influx/bin/activate
    PYTHON=python3.9
else
    source activate $CONDA_ENV_NAME
    PYTHON=python
fi
export PYTHONUNBUFFERED=yes

# $PYTHON $GFCL --addr $IP_ADDRESS --port 1234 --outdir $ODIR/RPG$IP_LAST_OCTET/35mV/ --wformno 1000
$PYTHON $GFCL --addr $IP_ADDRESS --port 1234 --outdir $ODIR/RPG101/35mV/ --wformno 1000