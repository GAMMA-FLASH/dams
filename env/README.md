# gammaflash-env
gammaflash-env

## Install and run the environment

1. Install python3 (current supported version 3.8.8)

2. Create the environment

    ```
    python3 -m venv /path/to/new/virtual/environment
    ```

3. Install requirements

    ```
    pip install -r venv/requirements.txt
    ```

4. Run the activate script

    ```
    source /path/to/new/virtual/environment/bin/activate
    ```

---

## Docker image

* Build the image
    ```
    docker build -t dams_image:1.6.0 .
    ```

----- entrypoint with jupyter start -----
Starts jupyter in the entrypoint and defines in bashrc the envvars DAMS, RPG_CONFIG

docker run -it -d \ 
    -v /data02/:/data02/ -v /data01/:/data01/ -v /home/user/dams:/home/usergamma/dams \
    --entrypoint /home/usergamma/dams/env/entrypoint.sh \ 
    -e DAMS=/home/usergamma/dams -e RPG_CONFIG=/home/usergamma/dams/setup/<CHOOSE_SETUP_HERE> \
    -p 8095:8888 --name gsky \
    gammaflash:1.5.0_gammasky /bin/bash

-----------------------------------------
