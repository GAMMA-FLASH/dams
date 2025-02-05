# __Prototype data processor pipe Gamma Flash__

## Prepare your workspace

1. Build the image and exec the container mounting the folders for data.

    ```[bash]
    cd env

    docker build -t dams_image .

    docker run  -it \
        -v /scratch/GAMMAFLASH/CIMONE/DL0:/home/gamma/workspace/Data/DL0 \
        -v /host-machine/path/to/DL1:/home/gamma/workspace/Data/DL1 \
        -v /host-machine/path/to/DL2:/home/gamma/workspace/Data/DL2 \
        -v /host-machine/path/to/Out/json:/home/gamma/workspace/Out/json \
        -v /host-machine/path/to/Out/logs:/home/gamma/workspace/Out/logs \
        -v /host-machine/path/to/dams:/home/gamma/workspace/dams
    ```

    e.g. for GAMMAFLASH data.

    ```[bash]
    docker run  -it \
        -v /archive/GAMMAFLASH/CIMONE/DL0:/home/gamma/workspace/Data/DL0 \
        -v /archive/GAMMAFLASH/DL1:/home/gamma/workspace/Data/DL1 \
        -v /archive/GAMMAFLASH/DL2:/home/gamma/workspace/Data/DL2 \
        -v /archive/GAMMAFLASH/logs:/home/gamma/workspace/Out/logs \
        -v /archive/GAMMAFLASH/OutJson:/home/gamma/workspace/Out/json \
        -v /host-machine/path/to/dams:/home/gamma/workspace/dams \
        --name dams_pipe dams_image:latest /bin/bash
    ```

2. Then you can add all the folder in this directory as shown below:

    ```[bash]
    ~
    |-- dependencies
    |   |-- gamma-env
    |   `-- rta-dataprocessor
    |       |-- env
    |       |-- gui
    |       |-- rtadp-proto
    |       |-- test
    |       |-- testavro
    |       |-- testpubsub
    |       |-- testpushpull
    |       `-- workers
    `-- workspace
        |-- Data
        |   |-- DL0
        |   |-- DL1
        |   `-- DL2
        |-- Out
        |   |-- json
        |   `-- logs
        `-- dams
            |-- dam
            |-- dl0
            |-- dl1
            |-- dl2
            |-- env
            |-- influxdb
            |-- pipe
            |-- setup
            |-- telegraf
            `-- test
    ```

3. Finally type

    ```[bash]
    cd pipe
    ```

    and you are ready to start

## Start the pipe processing

To start your DAMS pipe you can use the following python script as follow:
```[bash]
(gammaenv) [gamma@... pipe]$ python test_GammaFlash.py -h
```
```[bash]
usage: test_GammaFlash.py [-h] [-N {0,1,2,3,4,5,10,20}] [-dl0 PATH_DL0] [-dl1 PATH_DL1] [-dl2 PATH_DL2] [-jr PATH_JSON_RESULT]
                          [-spub SOCKET_DL0PUB] [-scck SOCKET_CCK] [-f JSON_PATH] [-c COMMAND_TYPE] [-t TARGET_PROCESSNAME]

Script to start various GammaFlash services.

options:
  -h, --help            show this help message and exit
  -N {0,1,2,3,4,5,10,20}, --service-number {0,1,2,3,4,5,10,20}
                        0: Start DL0Publisher 
                        1: Start DL0toDL2__service 
                        2: Start DL0toDL1__service 
                        3: Start DL1toDL2__service 
                        4: Start DL2Checker__service 
                        5: Start Publisher_CCK 
                        10: Start Monitoring 
                        20: Send command
  -dl0 PATH_DL0, --path-dl0 PATH_DL0
                        Path to DL0 data
  -dl1 PATH_DL1, --path-dl1 PATH_DL1
                        Path to DL1 data
  -dl2 PATH_DL2, --path-dl2 PATH_DL2
                        Path to DL2 data
  -jr PATH_JSON_RESULT, --path-json-result PATH_JSON_RESULT
                        Path to JSON results
  -spub SOCKET_DL0PUB, --socket-dl0pub SOCKET_DL0PUB
                        Socket for DL0Publisher
  -scck SOCKET_CCK, --socket-cck SOCKET_CCK
                        Socket for DL2Publisher
  -f JSON_PATH, --json-path JSON_PATH
                        Path to JSON configuration
  -c COMMAND_TYPE, --command-type COMMAND_TYPE
                        Command type for sending command
  -t TARGET_PROCESSNAME, --target-processname TARGET_PROCESSNAME
                        Target process name for sending command
  -d DETECTOR_CONFIG, --detector-config DETECTOR_CONFIG
                        Detectort configuration file path.
```

1. Start the three DL services:

    Open 3 new terminals and lanch the `.py` script, one in each new terminal:

    * __DL0toDL2__ service

    ```[bash]
    ./test_GammaFlash.py -N 1
    ```

    * __DL0toDL1__ service

    ```[bash]
    ./test_GammaFlash.py -N 2
    ```

    * __DL1toDL2__ service

    ```[bash]
    ./test_GammaFlash.py -N 3
    ```

    * __DL1.DL2vsDL2__ checker service

    ```[bash]
    ./test_GammaFlash.py -N 4
    ```

3. The pipe is still waiting the start command, so open a new terminal, let's place to the `workers` folder and type the start command:

    ```[bash]
    ./test_GammaFlash.py -N 20 -c <command_type> -t <pidtarget_process>
    ```

    e.g.:
    * `./test_GammaFlash.py -N 20 -c start -t all`
    * `./test_GammaFlash.py -N 20 -c cleanedshutdown -t all`

4. Now you can start the Publisher service

    * Publisher service

    ```[bash]
    ./test_GammaFlash.py -N 0
    ```

## Simple test pipeline

```[bash]
python test_GammaFlash.py -N 1 

python test_GammaFlash.py -N 2

python test_GammaFlash.py -N 3

python test_GammaFlash.py -N 30 -d /home/gamma/workspace/dams/dl1/dl02dl1_config_PMT.json -t all

python test_GammaFlash.py -N 20 -c start -f /home/gamma/workspace/dams/pipe/config.json -t all

python test_GammaFlash.py -N 0 -dl0 /home/gamma/workspace/Data/tmp/DL0 -dl1 /home/gamma/workspace/Data/tmp/DL1 -dl2 /home/gamma/workspace/Data/tmp/DL2

```

To stop the pipeline
```[python]
python test_GammaFlash.py -N 20 -c stop -f /home/gamma/workspace/dams/pipe/config.json -t all

python test_GammaFlash.py -N 20 -c cleanedshutdown -f /home/gamma/workspace/dams/pipe/config.json -t all
```