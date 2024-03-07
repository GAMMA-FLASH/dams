# __Prototype data processor pipe Gamma Flash__

## Prepare your workspace

1. Install the git repo [RTA Data Processor](https://github.com/ASTRO-EDU/rta-dataprocessor/tree/main), start the docker by linking these folders:
    * workspace
    * path/to/Data/data02
    * path/to/Data/DL0

    ```
    docker run -it -d -v /path/to/rta-dataprocessor/:/home/worker/workspace -v /path/to/data/data02:/data02/ -v /path/to/dams/:/home/worker/workspace/testgammaflash/dams/ -v path/to/data/DL0:/home/worker/workspace/testgammaflash/Data/data00 -p 8001:8001 --name ooqs1 worker:1.0.0_agileobs /bin/bash
    ```

    It will be generated a folder in `rta-dataprocessor` like the following:
    ```
    testgammaflah
    ├───dams
    ├───Data
    │   └───data00
    ```

2. Then you can add all the folder in this directory as shown below:

    ```
    testgammaflah
    ├───dams
    ├───Data
    │   └───data00
    ├───DL0toDL1__service
    ├───DL0toDL2__service
    ├───DL1toDL2__service
    ├───DL2Checker__service
    ├───env
    ├───Out
    │   ├───data01
    │   ├───data02
    │   └───json
    ```

    N.B.: Could be necessary to install `astropy` in the python venv

3. Finally type
    ```
    cd testgammaflash
    ```
    and you are ready to start

## Start the pipe processing

1. Prepare the script for the pipe services, `test_GammaFlash.sh`:

    ```
    path_dl0='/path/to/data/DL0' 
    path_dl1='/path/to/data/DL1/Out' 
    path_dl2='/path/to/data/DL2/Out' 
    path_json_result='/path/to/Out/json'
    socket='tcp://localhost:5555'
    socket_cck='tcp://localhost:5559'
    json_path='/path/to/config.json'
    ```

2. Start the three DL services:

    Open 3 new terminals and lanch the `.sh` script, one in each new terminal:

    * __DL0toDL2__ service
    ```
    ./test_GammaFlash.py 1
    ```

    * __DL0toDL1__ service
    ```
    ./test_GammaFlash.py 2
    ```

    * __DL1toDL2__ service
    ```
    ./test_GammaFlash.py 3
    ```

    * __DL1.DL2vsDL2__ checker service
    ```
    ./test_GammaFlash.py 4
    ```

3. The pipe is still waiting the start command, so open a new terminal, let's place to the `workers` folder and type the start command:

    ```
    cd worker
    python Command.py ../testgammaflash/config.json start all
    ```

4.  Now you can start the Publisher service

    * Publisher service
    ```
    ./test_GammaFlash.py 1
    ```
