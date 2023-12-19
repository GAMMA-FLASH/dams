#!/bin/bash

show_usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -h             Display this help message"
    echo "  -signal_number Specify the signal number to send to the process (optional)"
    echo "                 If not specified, the default signal is used."
}

# Check if the script is called with -h
if [ "$1" == "-h" ]; then
    show_usage
    exit 0
fi

signal_number=$1  # Get the last argument
# Check if the last argument is a valid number
if [ -n "$signal_number" ] && ! [[ "$signal_number" =~ ^[0-9]+$ ]]; then
    echo "Invalid Signal: $signal_number is not a number."
    exit 1
fi

if [ "$(hostname)" = "gamma-flash.iasfbo.inaf.it" ]; then
    # Source the virtual environment (uncomment if needed)
    # source ~/venvs/gammaflash-influx/bin/activate
    PYTHON=python3.9
    
else
    PYTHON=python
fi
GFCL="$PYTHON gfcl.py"

# Use pgrep to find processes based on the specified pattern
pids=$(pgrep -f "$GFCL")

# Check if any matching processes were found
if [ -n "$pids" ]; then
    # Kill the corresponding processes
    for pid in $pids; do
        echo "Terminating process with PID: $pid"
        kill $signal_number "$pid"
    done
else
    echo "No matching processes found."
fi