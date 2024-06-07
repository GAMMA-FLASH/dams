#!/bin/bash
export PYTHONPATH=/home/usergamma/workspace/rta-dataprocessor/workers:/home/usergamma/workspace:/home/usergamma/workspace/dams/dl1

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
# path_dl0='/home/worker/workspace/testgammaflash/Data/DL0/acquisizione_2022_06_24' 
# Define Socket Address
socket='tcp://127.0.0.1:5555'
socket_cck='tcp://127.0.0.1:5559'
# Define DL path
path_dl0='/home/usergamma/workspace/test/Data/DL0/' 
path_dl1='/home/usergamma/workspace/test/Data/DL1/' 
path_dl2='/home/usergamma/workspace/test/Data/DL2/' 
# Define Out JSON path
path_json_result='/home/usergamma/workspace/test/Out'
# Define config JSON path for RTA-Dataprocessor
config_path='/home/usergamma/workspace/dams/pipe/config.json'
# Define log file path for RTA-Dataprocessor
log_path='/home/usergamma/workspace/dams/pipe/logs/logs.log'
# Time delay between two messages of the Publisher
time_sleep_inframessage=1

# Take argument in input
arg=$1
if [ $arg -eq 0 ]; then
    echo ========= START DL0Publisher ========
    python publisher_dl0.py ${path_dl0} ${path_dl1} ${path_dl2} ${socket} ${time_sleep_inframessage}
elif [ $arg -eq 1 ]; then
    echo ========= START DL0toDL2__service ========
    # rm -rf $path_dl2/*
    python -c "from DL0toDL2__service.Supervisor_dl0todl2 import Supervisor_DL0toDL2; Supervisor_DL0toDL2('$config_path', 'DL0toDL2').start()"
elif [ $arg -eq 2 ]; then
    echo ========= START DL0toDL1__service ========
    rm -rf /home/usergamma/workspace/test/Data/DL1/*
    python -c "from DL0toDL1__service.Supervisor_dl0todl1 import Supervisor_DL0toDL1; Supervisor_DL0toDL1('${config_path}', 'DL0toDL1').start()"
elif [ $arg -eq 3 ]; then
    echo ========= START DL1toDL2__service ========
    rm -rf /home/usergamma/workspace/test/Data/DL2/*
    python -c "from DL1toDL2__service.Supervisor_dl1todl2 import Supervisor_DL1toDL2; Supervisor_DL1toDL2('${config_path}', 'DL1toDL2').start()"
elif [ $arg -eq 4 ]; then
    echo ========= START DL2Checker ========
    rm -rf $path_json_result/*
    python -c "from DL2Checker__service.Supervisor_checker import Supervisor_DL2CCK; Supervisor_DL2CCK('${config_path}', 'DL2Checker').start()"
elif [ $arg -eq 5 ]; then
    echo ========= START DL2Publisher ========
    python publisher_CCK.py ${path_dl2} ${socket_cck} ${time_sleep_inframessage}
else
    echo "Unknown argument!"
fi
