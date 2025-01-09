#!/bin/bash

cd workspace/dams/dam


# Name of the process to check
PROCESS_NAME="dam"

# Check if the process is running
if pgrep -x "$PROCESS_NAME" > /dev/null
then
    # The process is running, stop it
    echo "The $PROCESS_NAME process is running. Stopping it..."
    pkill -x "$PROCESS_NAME"

    # Allow time for the process to terminate
    sleep 1
fi

overlay.sh v0.94

# Start the process
echo "Starting the $PROCESS_NAME process..."
nohup ./dam > dam.log 2>&1 &
