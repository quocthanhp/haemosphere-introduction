#!/bin/bash

PORT=6544


# Activate the Conda environment
source activate /haemosphere-env

# Get the current date and time to name the log file
current_date=$(date +"%Y-%m-%d_%H-%M-%S")
log_file="nohup_${current_date}.log"

#find pid with netstat 
#if netstat is not working need to install
PID=$(netstat -lnp | grep ":$PORT " | awk '{print $7}' | sed 's|/.*||')

if [ -z "$PID" ]; then
    echo "No process is using port $PORT."
else
    echo "Process $PID is using port $PORT."

    # kill PID process
    kill $PID

    # check the kill result and show message
    if [ $? -eq 0 ]; then
        echo "Process $PID has been killed."
    else
        echo "Failed to kill process $PID. You might need to run the script as root."
    fi
fi


# Run the pserve command with nohup and redirect stdout and stderr to the log file
echo "-----------------------------------------------------------------"
echo "Now starting server"
echo "server log displayed automatically."
echo "Press Ctrl+C for exit server log watching"
echo "-----------------------------------------------------------------"
nohup pserve /haemosphere/development.ini > "$log_file" 2>&1 &
sleep 3

tail -f $log_file
