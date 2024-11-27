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
# Define Socket Address
socket='tcp://127.0.0.1:5555'
socket_cck='tcp://127.0.0.1:5559'
### Define DL path
# /path/to/DL0/acquisizione_YYYY_MM_DD/
path_dl0='/home/usergamma/workspace/symlink_to_acquisizioni/'
# path_dl0='/home/usergamma/workspace/Data/DL0/'${acqs_dir}'/'
# /path/to/DL1/acquisizione_YYYY_MM_DD/
path_dl1='/home/usergamma/workspace/Data/DL1/'
# /path/to/DL2/acquisizione_YYYY_MM_DD/
path_dl2='/home/usergamma/workspace/Data/DL2/'
# path_dl2='/home/usergamma/workspace/Data/DL2/acquisizione_2022_08_03/'
# Define Out JSON path
# path_json_result='/home/usergamma/workspace/Data/OutJson'$acqs_dir
path_json_result='/home/usergamma/workspace/Data/OutJson'
# Define logs path
# path_logs='/home/usergamma/workspace/Data/logs/'$acqs_dir'_logs'
path_logs='/home/usergamma/workspace/Data/logs'
# Define config JSON path for RTA-Dataprocessor
config_path='/home/usergamma/workspace/dams/pipe/config.json'
# Time delay between two messages of the Publisher
time_sleep_inframessage=0.01

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
    # rm -rf /home/usergamma/workspace/test/Data/DL1/*
    # rm -rf $path_dl1/*
    python -c "from DL0toDL1__service.Supervisor_dl0todl1 import Supervisor_DL0toDL1; Supervisor_DL0toDL1('${config_path}', 'DL0toDL1').start()"
elif [ $arg -eq 3 ]; then
    echo ========= START DL1toDL2__service ========
    # rm -rf /home/usergamma/workspace/test/Data/DL2/*
    # rm -rf $path_dl2/*
    python -c "from DL1toDL2__service.Supervisor_dl1todl2 import Supervisor_DL1toDL2; Supervisor_DL1toDL2('${config_path}', 'DL1toDL2').start()"
elif [ $arg -eq 4 ]; then
    echo ========= START DL2Checker ========
    # rm -rf $path_json_result/*
    # mkdir $path_json_result
    python -c "from DL2Checker__service.Supervisor_checker import Supervisor_DL2CCK; Supervisor_DL2CCK('${config_path}', 'DL2Checker').start()"
elif [ $arg -eq 5 ]; then
    echo ========= START DL2Publisher ========
    python publisher_CCK.py ${path_dl2} ${socket_cck} ${time_sleep_inframessage}
else
    echo "Unknown argument!"
fi
