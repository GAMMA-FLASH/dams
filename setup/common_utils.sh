#!/bin/bash

log_message() {
    local message="$@"
    echo -e "\e[33m[INFO] \e[0m$message"
}

log_error() {
    local message="$@"
    echo -e "\e[31m[ERROR] \e[0m$message"
}

process_file_with_function() {
    local function_to_call="$1"

    if ! type -t "$function_to_call" &> /dev/null; then
        echo "Errore: La funzione '$function_to_call' non è definita."
        return 1
    fi

    # Leggere il file riga per riga e chiamare la funzione
    while IFS=',' read -r rp_name addr port wformno || [[ -n "$rp_name" ]]; do
        # Controlla se la linea contiene almeno un carattere non-spazio
        if [[ -n "$rp_name" ]]; then
            "$function_to_call" "$rp_name" "$addr" "$port" "$wformno"
        fi
    done < "$RPG_CONFIG"
}

log_line(){
    log_message $1 $2 $3 $4
}

read_file() {
    process_file_with_function log_line 
}
open_rtadp_monitoring() {
    $PYTHON $MONcom
}
submit_rtadp_dl0_dl1_dl2_consumers() {
    echo "DL0DL1com: $DL0DL1com"
    echo "DL1DL2com: $DL1DL2com"
    echo "FWcom: $FWcom"
    echo "python: $PYTHON"

    if [ -z "$RTADP_JSON_PATH" ]; then
        echo "RTADP_JSON_PATH not defined."
        exit 1
    fi
    if [[ -z "$DL1DIR" && -z "$DL2DIR" ]]; then
        log_error "RTA DP directories are not defined."
        exit 1
    fi
    log_message "RTADP_JSON_PATH is set to: $RTADP_JSON_PATH"
    # do NOT reduce code lines here ######
    # DL0DL1
    pids=$(get_python_pids "$component_dl0_dl1")
    if [ -z "$pids" ]; then
        log_message "Starting DL0DL1 component..."
        nohup setsid python -c "$DL0DL1com" > $RTADP_LOGS/log_$component_dl0_dl1.log 2>&1 &
        log_message "DL0DL1 component started with PID $!"
    else
        log_message "DL0DL1 component is already submitted with PIDs: $pids"
    fi

    # DL1DL2
    pids=$(get_python_pids "$component_dl1_dl2")
    if [ -z "$pids" ]; then
        log_message "Starting DL1DL2 component..."
        nohup setsid python -c "$DL1DL2com" > $RTADP_LOGS/log_$component_dl1_dl2.log 2>&1 &
        log_message "DL1DL2 component started with PID $!"
    else
        log_message "DL1DL2 component is already submitted with PIDs: $pids"
    fi

    # Forwarder
    pids=$(get_python_pids "$component_fw")
    if [ -z "$pids" ]; then
        log_message "Starting Forwarder component..."
        echo $FWcom
        nohup setsid $PYTHON $FWcom > $RTADP_LOGS/log_$component_fw.log 2>&1 &
        log_message "Forwarder component started with PID $!"
    else
        log_message "Forwarder component is already submitted with PIDs: $pids"
    fi
    # ######

    echo "All jobs submitted."
}

start_rtadp() {
    
    # Esegui lo script Python e ottieni l'exit code
    log_message "Waiting for RTADP startup done..."
    python "$DAMS/setup/wait_for_rtadp.py" "$RTADP_JSON_PATH" "60"
    exit_code=$?

    # Controlla l'exit code
    if [ $exit_code -eq 0 ]; then
        $PYTHON $SNDcom start all
        log_message "RTADP $command sent..."
    else
        log_error "Il processo 'wait_for_rtadp.py' non è terminato correttamente. Codice di uscita: $exit_code"
    fi
    echo $exit_code

}

stop_rtadp() {
    PIDS=$(get_rtadp_pids)
    # Check if any matching processes were found
    if [ -n "$PIDS" ]; then
        log_message "Cleaned shutdown rtadp pipeline"
        $PYTHON $SNDcom cleanedshutdown all
        sleep 2
        log_message "Stopping forwarder"
        pkill -f "Forwarder.py"
    else
        log_message "No rtadp processes found!"
    fi
}

get_python_pids() {
  local process_name_content=$1
  local filter1=$2
  local filter2=$3

#   echo "Looking for: $process_name_content $filter1 $filter2"

  # Usa un array per i filtri
  local filters=("$process_name_content")
  [[ -n "$filter1" ]] && filters+=("$filter1")
  [[ -n "$filter2" ]] && filters+=("$filter2")

  # Costruzione della pipeline dinamica
  local result=$(ps x | grep "$PYTHON" | grep "$process_name_content" | grep -v grep)

  for filter in "${filters[@]:1}"; do
    result=$(echo "$result" | grep "$filter")
  done

  # Estrai i PID e restituiscili
  echo "$result" | awk '{print $1}'
}


get_rtadp_pids() {
  local P1=$(get_python_pids $component_dl0_dl1)
  local P2=$(get_python_pids $component_dl1_dl2)
  local all_pids="$P1\n$P2" 
  echo -e "$all_pids" 
}

submit_job_once() {
    local component=$1
    local command=$2

    # Ottieni i PID dei processi esistenti per il componente
    local pids=$(get_python_pids "$component")

    # Se non ci sono PID, esegui il comando e registra il PID
    if [ -z "$pids" ]; then
        echo "Submitting '$command' 1"
        $command
        echo "Submitting '$command' 2"
        # eval "nohup setsid $command 2>&1 > /dev/null &"
    else
        log_message "$component is already submitted with PIDs: $pids"
    fi

    echo "done"
}

invalid_bg_fg_selection() {
    log_error "cannot start script with both options background and foreground: $1"; usage;
}

check_host_and_activate_python() {
if [ "$(cat /etc/hostname)" = "gamma-flash.iasfbo.inaf.it" ]; then
    
    PYTHON=python3.9
else
    log_message "activating conda env. '$CONDA_ENV_NAME'"
    source activate "$CONDA_ENV_NAME"
    PYTHON=python
fi
log_message "Using python v. ${PYTHON}"
}

handle_bg_fg_option() {
    local is_background=$1
    local rp_name=$2
    if [ -z "${bg_or_fg}" ]; then
        BACKGROUND=$is_background
        bg_or_fg=chosen
        ATTACHED_NAME="$rp_name"
    else
        invalid_bg_fg_selection
    fi
}

# Inizializza variabili
GFCL=${GFCL:-"$DAMS/dl0/gfcl.py"}
BACKGROUND=true
ATTACHED_NAME="all"
MULTIPROCESSING=""
CONDA_ENV_NAME="${CONDA_ENV_NAME:-"gammaflash"}"

RTADP_START=false
export PYTHONUNBUFFERED=true
####RTADP Configuration:
component_dl0_dl1="DL0toDL1"
component_dl1_dl2="DL1toDL2"
DL0DL1com="from DL0toDL1__service.Supervisor_dl0todl1 import Supervisor_DL0toDL1; Supervisor_DL0toDL1('${RTADP_JSON_PATH}', '${component_dl0_dl1}')"
DL1DL2com="from DL1toDL2__service.Supervisor_dl1todl2 import Supervisor_DL1toDL2; Supervisor_DL1toDL2('${RTADP_JSON_PATH}', '${component_dl1_dl2}')"

component_base="$HOME/dependencies/rta-dataprocessor/workers"
common_args="${RTADP_JSON_PATH}"

component_fw="Forwarder.py"
component_mon="ProcessMonitoring.py"
component_com="SendCommand.py"

FWcom="${component_base}/${component_fw} ${RTADP_JSON_PATH}"
MONcom="${component_base}/${component_mon} ${RTADP_JSON_PATH}"
SNDcom="${component_base}/${component_com} ${RTADP_JSON_PATH}"

# Se RPG_CONFIG è già definito come variabile d'ambiente, usala come valore predefinito
# Controllo che RPG_CONFIG sia stato definito, o se esiste già nella variabile d'ambiente

RPG_CONFIG="${RPG_CONFIG:-}"
# Controlla se RPG_CONFIG è definita e stampa un messaggio informativo
if [ -n "$RPG_CONFIG" ]; then
    log_message "RPG_CONFIG is set to: $RPG_CONFIG"
fi

cli_argparser () {
log_error "parsing args"
# Parsing degli argomenti della riga di comando
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --config|-c)
            RPG_CONFIG="$2"
            shift ;;
        --rtadp|-r)
            log_error "setting RTADP_START"
            RTADP_START=true ;;
        --background|-b) 
            handle_bg_fg_option true "$2"
            shift ;;
        --attached|-a)
            handle_bg_fg_option false "$2"
            shift ;;
        --multiprocessing|-m) MULTIPROCESSING="--multiprocessing" ;;
        --help|-h)
            usage; log_message "the currently selected file is: ";read_file;;
        *) log_error "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

# Controllo che RPG_CONFIG sia stato definito, o se esiste già nella variabile d'ambiente
if [ -z "$RPG_CONFIG" ]; then
    log_error "RPG_CONFIG not defined. Please set it as an environment variable or use --config."
    usage
    exit 1
fi
RPG_DEFAULT_FILE="RPGLIST.cfg"
if [ -d "$RPG_CONFIG" ]; then
    # Se è una directory, assegna file di configurazione predefinito
    RPG_CONFIG="$RPG_CONFIG/$RPG_DEFAULT_FILE"
fi
if [ ! -e "$RPG_CONFIG" ]; then
    log_error "Config file $RPG_CONFIG does not exist."
    usage
    exit 1
fi
# Risolvi il percorso assoluto per RPG_CONFIG
export RPG_CONFIG=$(readlink -f "$RPG_CONFIG")

echo -e "\033[0;32m -- Using Red Pitaya deployment configuration: $RPG_CONFIG\033[0m"
echo 

log_setup
}

log_error "ciao"