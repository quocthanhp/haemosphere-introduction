#!/bin/bash
PATH=/haemosphere-env/bin:/miniconda3/bin:/miniconda3/bin:/miniconda3/condabin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin

PORT=6544
#find pid with netstat 
#if netstat is not working need to install

#check alive if not run it
PID=$(netstat -lnp | grep ":$PORT " | awk '{print $7}' | sed 's|/.*||')

if [ -z "$PID" ]; then
    echo "[$current_date] No process is using port $PORT."
    # Activate the Conda environment
    source /miniconda3/bin/activate /haemosphere-env
    # Get the current date and time to name the log file
    current_date=$(date +"%Y-%m-%d_%H-%M-%S")
    log_file="/haemosphere/nohup_${current_date}.log"
    nohup pserve /haemosphere/development.ini > "$log_file" 2>&1 &
else
    echo "[$current_date] $PORT alive."
fi