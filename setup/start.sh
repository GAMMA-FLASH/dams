#!/bin/bash

build_gfcl_command() {
    local addr="$1"
    local port="$2"
    local rp_name="$3"
    local wformno="$4"

    # Costruisci e ritorna la stringa del comando
    echo "$PYTHON $GFCL --addr \"$addr\" --port \"$port\" --outdir \"$ODIR/RPG$rp_name/35mV/\" --wformno \"$wformno\" $MULTIPROCESSING"
}

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

# Variabile per tenere traccia del primo RPG
FIRST_RPG_NAME=""

# Itera su ogni riga del file di configurazione
while IFS=',' read -r rp_name addr port wformno || [[ -n "$addr" ]]; do
    # Memorizza il primo RPG
    if [ -z "$FIRST_RPG_NAME" ]; then
        FIRST_RPG_NAME="$rp_name"
    fi
    
    # Esecuzione del comando con i parametri letti
    if [ "$BACKGROUND" = true ]; then
        # Lancia in background
        command_string=$(build_gfcl_command $addr $port $rp_name $wformno)
        log_message "Client started with: \" $command_string\""
        nohup bash -c "$command_string" > "$DL0_LOGS/gfcl_RPG$rp_name.log" 2>&1 &
    elif [ "$ATTACHED_NAME" = "$rp_name" ] || ( [ -z "$ATTACHED_NAME" ] && [ "$rp_name" = "$FIRST_RPG_NAME" ] ); then
        # Lancia in foreground se corrisponde il nome o se ATTACHED_NAME è vuoto e corrisponde al primo RPG
        echo "Launched RPG: $rp_name"
        eval $(build_gfcl_command "$addr" "$port" "$rp_name" "$wformno")
        exit 0 # Esci dopo aver lanciato l'attached process
    fi
done < "$RPG_CONFIG"
