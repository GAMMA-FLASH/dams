#!/bin/bash

PIDS=gfcl.pids
DL0_LOGS=$DAMS/logs/dl0
CONDA_ENV_NAME="gammaflash"

source "$(dirname "$0")/.common"

# Check if ODIR is defined
if [ -z "$ODIR" ]; then
    echo "ODIR not defined"
    exit 1
else 
    log_message "ODIR is set to: $ODIR"
fi

# Check if DAMS is defined
if [ -z "$DAMS" ]; then
    echo "DAMS root not defined"
    exit 1
else 
    log_message "DAMS is set to: $DAMS"
fi

mkdir -p "$DL0_LOGS"


GFCL=${GFCL:-"$DAMS/dl0/gfcl.py"}
echo -e "\033[0;32m -- Using Client Script: ${GFCL}\033[0m"

cd "$DAMS/dl0" || exit

# Check if gfcl.ini exists
if [ -e "gfcl.ini" ]; then

    echo -e "\033[0;32m -- Using Gammaflash Client configuration: $(readlink -f gfcl.ini)\033[0m"
else
    echo "gfcl.ini not defined"
    exit 1
fi

if [ "$(cat /etc/hostname)" = "gamma-flash.iasfbo.inaf.it" ]; then
    PYTHON=python3.9
else
    source activate "$CONDA_ENV_NAME"
    PYTHON=python
fi

# Variabile per tenere traccia del primo RPG
FIRST_RPG_NAME=""

# Itera su ogni riga del file di configurazione
while IFS=',' read -r rp_name addr port wformno || [[ -n "$addr" ]]; do
    # Memorizza il primo RPG
    if [ -z "$FIRST_RPG_NAME" ]; then
        FIRST_RPG_NAME="$rp_name"
    fi

    # Creazione della directory di output
    mkdir -p "$ODIR/$rp_name/35mV/"
    
    # Esecuzione del comando con i parametri letti
    if [ "$BACKGROUND" = true ]; then
        # Lancia in background
        nohup $PYTHON $GFCL --addr "$addr" --port "$port" --outdir "$ODIR/$rp_name/35mV/" --wformno "$wformno" $MULTIPROCESSING > "$DL0_LOGS/gfcl_$rp_name.log" 2>&1 &
        log_message "\"$GFCL\" started with --addr "$addr" --port "$port" --outdir "$ODIR/$rp_name/35mV/" --wformno "$wformno" $MULTIPROCESSING. Logs in "$DL0_LOGS/gfcl_$rp_name.log""
    elif [ "$ATTACHED_NAME" = "$rp_name" ] || ( [ -z "$ATTACHED_NAME" ] && [ "$rp_name" = "$FIRST_RPG_NAME" ] ); then
        # Lancia in foreground se corrisponde il nome o se ATTACHED_NAME è vuoto e corrisponde al primo RPG
        echo "Launched RPG: $rp_name"
        $PYTHON $GFCL --addr "$addr" --port "$port" --outdir "$ODIR/$rp_name/35mV/" --wformno "$wformno" $MULTIPROCESSING
        exit 0 # Esci dopo aver lanciato l'attached process
    fi
done < "$RPG_CONFIG"
