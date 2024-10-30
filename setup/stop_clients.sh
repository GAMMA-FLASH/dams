#!/bin/bash

SIGNAL="2"
source "$(dirname "$0")/.common"

# Check if DAMS is defined
if [ -z "$DAMS" ]; then
    echo "DAMS root not defined"
    exit 1
fi

get_clients_pids() {
    local ip=$1
    local GFCL="gfcl.py"
    ps aux | grep $PYTHON | grep $GFCL | grep "$ip" | grep -v grep | awk '{print $2}'
}

wait_for_termination() {
    local pid=$1
    local timeout_sec=10
    local timeout=$timeout_sec

    while kill -0 "$pid" 2>/dev/null; do
        if [ $timeout -le 0 ]; then
            echo "Process $pid did not terminate in ${timeout_sec} seconds. Sending SIGKILL."
            kill -9 "$pid"
            break
        fi
        sleep 1
        timeout=$((timeout - 1))
    done

    if ! kill -0 "$pid" 2>/dev/null; then
        echo "Client with PID $pid terminated."
    else
        echo "Failed to gracefully terminate Client with PID $pid."
    fi
}

terminate_client() {
    local X=$1

    PIDS=$(get_clients_pids "$X")

    # Check if any matching processes were found
    if [ -n "$PIDS" ]; then
        # Kill the corresponding processes
        for pid in $PIDS; do
            log_message "Terminating Client with RP ip $X [PID $pid]"
            kill "-${SIGNAL}" "${pid}"
            wait_for_termination "$pid" &
        done
        wait
    else
        echo "No matching processes found for RPID $X."
    fi
}

log_message "Stopping gammaflash clients" 

while IFS=',' read -r rp_name addr port wformno || [[ -n "$rp_name" ]]; do
    if [ -z "$ATTACHED_NAME" ] || [ "$ATTACHED_NAME" = "$rp_name" ]; then
        # Termina il rp specificato
        terminate_client "$addr" &

        # Se è stato specificato un solo RPG, esci dal ciclo
        if [ -n "$ATTACHED_NAME" ]; then
            break  # Esci solo dal ciclo, non dallo script
        fi
    fi
done < "$RPG_CONFIG"

wait

