#!/bin/bash

# Check if DAMS is defined
if [ -z "$DAMS" ]; then
    echo "DAMS root not defined"
    exit 1
fi

help() {
    echo "Usage: $0 [--signal <signal_number>] [--rpid <ip_address>] [--ip <ip_address>] ..."
    echo "Options:"
    echo "  -h             Display this help message"
    echo "  --signal, -s   Specify the signal number to send to the process (optional). Default SIGINT"
    echo "  --rpid,   -r   The client to kill acquiring from the specified rp ID. (optional). Default 'all'"
}

get_clients_pids() {
    local X=$1
    local GFCL="gfcl.py"
    ps aux | grep $PYTHON | grep $GFCL | grep "$X" | grep -v grep | awk '{print $2}'
}

terminate_client() {
    local X=$1

    PIDS=$(get_clients_pids "$X")

    # Check if any matching processes were found
    if [ -n "$PIDS" ]; then
        # Kill the corresponding processes
        for pid in $PIDS; do
            echo "Terminating Client with RPID $X [PID $pid]"
            kill "-${SIGNAL}" "${pid}"
        done
        for pid in $PIDS; do
            # Wait for the process to terminate
            while kill -0 "$pid" 2>/dev/null; do
                sleep 1
                # echo "Waiting for process $pid to terminate..."
            done
            echo "Client RPID $X [PID $pid] terminated."
        done
    else
        echo "No matching processes found for RPID $X."
    fi
}

POSITIONAL_ARGS=()
RP_IPS=()
SIGNAL="2"

while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--rpid)
            RP_IPS+=("$2")
            shift # past argument
            shift # past value
            ;;
        -s|--signal_number)
            SIGNAL="$2"
            shift # past argument
            shift # past value
            ;;
        -*|--*)
            echo "Unknown option $1"
            help
            exit 1
            ;;
        *)
            POSITIONAL_ARGS+=("$1") # save positional arg
            shift # past argument
            ;;
    esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

# Check if the last argument is a valid number
if [ -n "$SIGNAL" ] && ! [[ "$SIGNAL" =~ ^[0-9]+$ ]]; then
    echo "Invalid Signal: $SIGNAL is not a number."
    exit 1
fi

if [[ -n ${POSITIONAL_ARGS[0]} ]]; then
    echo "Last line of file specified as non-opt/last argument:"
    SIGNAL=${POSITIONAL_ARGS[0]}
fi


if [ ${#RP_IPS[@]} -eq 0 ]; then
    RP_IPS[0]="all"
fi

echo "Stopping gammaflash clients with:" 
echo " Signal     = ${SIGNAL}"
echo " RP IDS = ${RP_IPS[@]}"

if [ "$(cat /etc/hostname)" = "gamma-flash.iasfbo.inaf.it" ]; then
    # Source the virtual environment (uncomment if needed)
    # source ~/venvs/gammaflash-influx/bin/activate
    PYTHON=python3.9
else
    PYTHON=python
fi

terminate_in_parallel() {
    for client in "$@"; do
        terminate_client "$client" &
    done
    wait
}

if [[ ${#RP_IPS[@]} -eq 1 && "${RP_IPS[0],,}" == "all"  ]]; then
    terminate_in_parallel {101..106}
else
    for ip in "${RP_IPS[@]}"; do
        if [[ $ip =~ ^10[1-6]$ ]]; then
            terminate_client "$ip" &
        else
            echo "Invalid argument. Please provide a number between 101 and 106."
        fi
    done
    wait
fi
