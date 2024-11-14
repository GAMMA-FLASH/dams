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

=============
Docker image

docker system prune

-----

On MAC platform
docker build --platform linux/amd64 -t gammaflash:1.5.0 -f ./Dockerfile.amd .
docker build --platform linux/arm64 -t gammaflash:1.6.0 -f ./Dockerfile.arm .


On Linux platform
docker build -t gammaflash:1.5.0 -f ./Dockerfile.amd .

-----

docker build -t gammaflash:1.2.0 .

./bootstrap.sh gammaflash:1.2.0 agileobs

docker run -it -d -v /home/agileobs/gammaflash/:/home/usergamma/workspace -v /data02/:/data02/  -p 8001:8001 --name gf gammaflash:1.2.0_agileobs /bin/bash

docker exec -it gf /bin/bash
cd
. entrypoint.sh

nohup jupyter-lab --ip="*" --port 8001 --no-browser --autoreload --NotebookApp.token='gf2023#'  --notebook-dir=/home/usergamma/workspace --allow-root > jupyterlab_start.log 2>&1 &

----- entrypoint with jupyter start -----
Starts jupyter in the entrypoint and defines in bashrc the envvars DAMS, RPG_CONFIG

docker run -it -d \ 
    -v /data02/:/data02/ -v /data01/:/data01/ -v /home/user/dams:/home/usergamma/dams \
    --entrypoint /home/usergamma/dams/env/entrypoint.sh \ 
    -e DAMS=/home/usergamma/dams -e RPG_CONFIG=/home/usergamma/dams/setup/<CHOOSE_SETUP_HERE> \
    -p 8095:8888 --name gsky \
    gammaflash:1.5.0_gammasky /bin/bash

-----------------------------------------
