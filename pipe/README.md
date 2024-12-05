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

1. Prepare the script for the pipe services, `test_GammaFlash.sh`:

    ```[bash]
    path_dl0='/path/to/data/DL0' 
    path_dl1='/path/to/data/DL1/Out' 
    path_dl2='/path/to/data/DL2/Out' 
    path_json_result='/path/to/Out/json'
    socket='tcp://localhost:<port>'
    json_path='/path/to/config.json'
    ```

2. Start the three DL services:

    Open 3 new terminals and lanch the `.sh` script, one in each new terminal:

    * __DL0toDL2__ service

    ```[bash]
    ./test_GammaFlash.py 1
    ```

    * __DL0toDL1__ service

    ```[bash]
    ./test_GammaFlash.py 2
    ```

    * __DL1toDL2__ service

    ```[bash]
    ./test_GammaFlash.py 3
    ```

    * __DL1.DL2vsDL2__ checker service

    ```[bash]
    ./test_GammaFlash.py 4
    ```

3. The pipe is still waiting the start command, so open a new terminal, let's place to the `workers` folder and type the start command:

    ```[bash]
    cd worker
    python SendCommand.py <config_file> <command_type> <pidtarget_processname>
    ```

    e.g. `python SendCommand.py /home/gamma/workspace/dams/pipe/config.json start all`

4. Now you can start the Publisher service

    * Publisher service

    ```[bash]
    ./test_GammaFlash.py 0
    ```
