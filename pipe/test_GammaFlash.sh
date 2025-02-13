#!/bin/bash

if [ "$#" -eq 0 ]; then
    echo "Usage: ./test_GammaFlash.py N"
    echo "  N=0         start DL0Publisher"
    echo "  N=1         start DL0toDL2__service"
    echo "  N=2         start DL0toDL1__service"
    echo "  N=3         start DL1toDL2__service"
    echo "  N=4         start DL2Checker__service"
    echo "  N=5         start Publisher_CCK"
    exit 0
fi

path_dl0='/home/gamma/workspace/Data/tmpscratch/DL0' 
path_dl1='/home/gamma/workspace/Data/tmpscratch/DL1' 
path_dl2='/home/gamma/workspace/Data/DL2' 
path_json_result='/home/gamma/workspace/Data/Out/json'
socket='tcp://localhost:5555'
socket_cck='tcp://localhost:5559'
json_path='/home/gamma/workspace/dams/pipe/config.json'

# Take argument in input
arg=$1
if [ $arg -eq 0 ]; then
    echo ========= START DL0Publisher ========
    python publisher_dl0.py ${path_dl0} ${path_dl1} ${path_dl2} ${socket} 3
elif [ $arg -eq 1 ]; then
    echo ========= START DL0toDL2__service ========
    rm -rf $path_dl2/*
    python -c "from DL0toDL2__service.Supervisor_dl0todl2 import Supervisor_DL0toDL2; Supervisor_DL0toDL2('$json_path', 'DL0toDL2')"
elif [ $arg -eq 2 ]; then
    echo ========= START DL0toDL1__service ========
    rm -rf $path_dl1/*
    python -c "from DL0toDL1__service.Supervisor_dl0todl1 import Supervisor_DL0toDL1; Supervisor_DL0toDL1('${json_path}', 'DL0toDL1')"
elif [ $arg -eq 3 ]; then
    echo ========= START DL1toDL2__service ========
    rm -rf $path_dl2/*
    python -c "from DL1toDL2__service.Supervisor_dl1todl2 import Supervisor_DL1toDL2; Supervisor_DL1toDL2('${json_path}', 'DL1toDL2')"
elif [ $arg -eq 4 ]; then
    echo ========= START DL2Checker ========
    rm -rf $path_json_result/*
    python -c "from DL2Checker__service.Supervisor_checker import Supervisor_DL2CCK; Supervisor_DL2CCK('${json_path}', 'DL2Checker').start()"
elif [ $arg -eq 5 ]; then
    echo ========= START DL2Publisher ========
    python publisher_CCK.py ${path_dl2} ${socket_cck}
else
    echo "Unknown argument!"
fi