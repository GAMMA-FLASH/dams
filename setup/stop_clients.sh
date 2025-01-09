#!/bin/bash

usage() {
    log_message "Usage: $0 [--config <RPG_config_or_directory>] [--attached [RPGNAME]]"
    log_message "Usage: $0 [-c <RPG_config_or_directory>] [-a [RPGNAME]]"
    log_message "RPGNAME one of the ones defined in .cfg"
    exit 1
}

log_setup() {
    echo
    log_message "Stopping gammaflash clients. Selected rpId: '${ATTACHED_NAME}'"
    log_message "Stop rtadp: ${RTADP_START}"
    echo
}

stop_rtadp_async () {
    sleep_s=10
    if [ "$RTADP_START" == "true" ]; then 
        log_message "rtadp will stop in $sleep_s seconds ..."
        sleep $sleep_s
        echo 
        log_message "Time to stop rtadp..."
        stop_rtadp 
    fi
}

SIGNAL="2"
source "$(dirname "$0")/common_utils.sh"
check_host_and_activate_python
cli_argparser $@
# Check if DAMS is defined
if [ -z "$DAMS" ]; then
    echo "DAMS root not defined"
    exit 1
fi

wait_for_termination() {
    local pid=$1
    local timeout_sec=20
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
        log_message "Client with PID $pid terminated."
    else
        log_error "Failed to gracefully terminate Client with PID $pid."
    fi
}

terminate_client() {
    local ID=$1
    local addr=$2
    local port=$3
    
    PIDS=$(get_python_pids "$GFCL" "$addr" "$port")
    # Check if any matching processes were found
    if [ -n "$PIDS" ]; then
        # Kill the corresponding processes
        for pid in $PIDS; do
            log_message "Terminating Client with RPID $ID at ip $addr:$port [PID $pid]"
            kill "-${SIGNAL}" "${pid}"
            wait_for_termination "$pid" &
        done
        wait
    else
        log_message "No matching processes found for RPID $addr:$port."
    fi
}

check_client_to_terminate () {
    ### "$rp_name" "$addr" "$port" "$wformno"
    local rp_name=$1
    local addr=$2
    local port=$3
    local wformno=$4
    if [ -z "$ATTACHED_NAME" ] || [ "$ATTACHED_NAME" = "$rp_name" ] || [ "$ATTACHED_NAME" = "all" ]; then
        # Termina il rp specificato
        terminate_client "$rp_name" "$addr" "$port" &
    fi
}

process_file_with_function check_client_to_terminate

wait

stop_rtadp_async &
