#!/bin/bash

# Funzione per mostrare l'uso dello script


usage() {
    log_message "Usage: $0 [--config <RPG_config_or_directory>] [[--background [RPGNAME|all]] or [--attached [RPGNAME]]] [--multiprocessing] [--rtadp]"
    log_message "Usage: $0 [-c <RPG_config_or_directory>] [[-b [RPGNAME|all]] or [-a [RPGNAME]]] [-m] [-r]"
    log_message "RPGNAME one of the ones defined in .cfg or 'all'"
    exit 1
}

build_gfcl_command() {
    local addr="$1"
    local port="$2"
    local rp_name="$3"
    local wformno="$4"

    # Costruisci e ritorna la stringa del comando
    echo "$PYTHON $GFCL --rpid \"$rp_name\" --addr \"$addr\" --port \"$port\" --outdir \"$DL0DIR/RPG$rp_name/35mV/\" --wformno \"$wformno\" $MULTIPROCESSING"

}

log_setup() {
    echo
    log_message "Background execution: ${BACKGROUND}"
    log_message "Starting rpId: ${ATTACHED_NAME}"
    log_message "Client multiprocessing rtadp: ${RTADP_START}"
    log_message "Starting rtadp: ${RTADP_START}"
    echo
}

source "$(dirname "$0")/common_utils.sh"
check_host_and_activate_python

cli_argparser $@
# Itera su ogni riga del file di configurazione
check_client_to_start () {
    ### "$rp_name" "$addr" "$port" "$wformno"
    local rp_name=$1
    local addr=$2
    local port=$3
    local wformno=$4
    # Memorizza il primo RPG
    if [ -z "$FIRST_RPG_NAME" ]; then
        FIRST_RPG_NAME="$rp_name"
    fi
    
    # Esecuzione del comando con i parametri letti
    if [ "$BACKGROUND" = true ]; then
        if [ "$ATTACHED_NAME" = "$rp_name" ] || [ "$ATTACHED_NAME" = "all" ]; then
            command_string=$(build_gfcl_command $addr $port $rp_name $wformno)
            log_message "Client started with: \" $command_string\""
            nohup bash -c "$command_string" > "$DL0_LOGS/gfcl_RPG$rp_name.log" 2>&1 &
        fi
        
    elif [ "$ATTACHED_NAME" = "$rp_name" ] || ( [ -z "$ATTACHED_NAME" ] && [ "$rp_name" = "$FIRST_RPG_NAME" ] ); then
        echo "Launched RPG: $rp_name"
        eval $(build_gfcl_command "$addr" "$port" "$rp_name" "$wformno")

        log_error "do not passhere"
        stop_rtadp 
        exit 0 # Esci dopo aver lanciato l'attached process
    fi
}




PIDS=gfcl.pids
DL0_LOGS=$DAMS/logs/dl0
RTADP_LOGS=$DAMS/logs/rtadp


# Check if DL0DIR is defined
if [ -z "$DL0DIR" ]; then
    echo "DL0DIR not defined"
    exit 1
else 
    log_message "DL0DIR is set to: $DL0DIR"
fi

# Check if DAMS is defined
if [ -z "$DAMS" ]; then
    echo "DAMS root not defined"
    exit 1
else 
    log_message "DAMS is set to: $DAMS"
fi

mkdir -p "$DL0_LOGS"
mkdir -p "$RTADP_LOGS"

test_gammaflash=${test_gammaflash:-"$DAMS/pipe/test_GammaFlash.sh"}
echo -e "\033[0;32m -- Using Client Script: ${GFCL}\033[0m"
echo -e "\033[0;32m -- Using Pipe Script: ${test_gammaflash}\033[0m"
cd "$DAMS/dl0" || exit

# Check if gfcl.ini exists
if [ -e "gfcl.ini" ]; then

    echo -e "\033[0;32m -- Using Gammaflash Client configuration: $(readlink -f gfcl.ini)\033[0m"
else
    echo "gfcl.ini not defined"
    exit 1
fi
# export PYTHONUNBUFFERED="false"
# DL0DL1="python -c "from DL0toDL1__service.Supervisor_dl0todl1 import Supervisor_DL0toDL1; Supervisor_DL0toDL1('${json_path}', 'DL0toDL1').start()""
# DL1DL2="3"
echo "going on"
# Variabile per tenere traccia del primo RPG
FIRST_RPG_NAME=""

# submit_rtadp_dl0_dl1_dl2_consumers
echo "calling the function"
submit_rtadp_dl0_dl1_dl2_consumers
echo "done.."
# sleep 10
if [ $RTADP_START == true ]; then
start_rtadp
else 
log_message "start manually rtadp"
fi
process_file_with_function check_client_to_start
