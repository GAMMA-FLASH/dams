# gamma-env
gamma-env

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

# Docker image

Build the images using docker compose:
it will build base and prod image.
* `base` image hase no source code, it must be mounted from host
    ```[bash]
    docker compose build base
    ```
* `prod` image comes with source code and testlab setup installed.  
    Note: check dams setup  
    Note: `latest` image has source code from `main` branch
    ```[bash]
    docker compose build prod
    ```
    to build installing a specified **branch**, or **tagged** dams version:
    ```[bash]
    REPO_BRANCH=<branch> docker compose build prod
    ```
**example**: to build all images; prod with the current host working branch:
```[bash]
REPO_BRANCH=$(git rev-parse --abbrev-ref HEAD) docker compose build
```

## Start development environment using base image:
----- entrypoint with jupyter start -----

Starts jupyter in the entrypoint and defines in bashrc the envvars DAMS, RPG_CONFIG. 

1.  bootstrap docker image to allow docker to write on host:
    ./bootstrap.sh dams_{image}:latest $USER

2.  mount all the archives you need to write data and logs:
    bond a port for opening jupyter notebook

    ```[bash]
    docker run  -it -d \
        -v /archive/.../DL0:/home/gamma/workspace/Data/DL0  \
        -v /archive/.../DL1:/home/gamma/workspace/Data/DL1  \
        -v /archive/.../DL2:/home/gamma/workspace/Data/DL2  \
        -v /archive/.../logs:/home/gamma/workspace/Out/logs \
        -v /archive/.../OutJson:/home/gamma/workspace/Out/json  \
        -v /path/to/.../dams:/home/gamma/workspace/dams \
        --entrypoint /home/gamma/workspace/dams/env/entrypoint.sh \
        -e DAMS=/home/gamma/workspace/dams \
        -e RPG_CONFIG=/home/gamma/workspace/dams/setup/testlab \
        -p 8101:8888    \
        --name dams_pipe_project \
        dams_base:latest_$USER \
        /bin/bash
    ```

3.  to enter the container:
    ```[bash]
    docker exec -it dams_pipe_project bash
    ```
-----------------------------------------

## Start production environment using prod image:

----- entrypoint with jupyter start -----

Starts jupyter in the entrypoint and defines in bashrc the envvars DAMS, RPG_CONFIG. 

1.  bootstrap docker image to allow docker to write on host:
    ```[bash]
    ./bootstrap.sh dams_{image}:latest $USER
    ```

2.  mount all the archives you need to write data and logs:
    bond a port for opening jupyter notebook

    ```[bash]
    docker run  -it -d \
        -v /archive/.../DL0:/home/gamma/workspace/Data/DL0  \
        -v /archive/.../DL1:/home/gamma/workspace/Data/DL1  \
        -v /archive/.../DL2:/home/gamma/workspace/Data/DL2  \
        -v /archive/.../logs:/home/gamma/workspace/Out/logs \
        -v /archive/.../OutJson:/home/gamma/workspace/Out/json  \
        --entrypoint /home/gamma/workspace/dams/env/entrypoint.sh \
        -e DAMS=/home/gamma/workspace/dams \
        -e RPG_CONFIG=/home/gamma/workspace/dams/setup/testlab \
        -e OSC_CONFIG=/home/gamma/workspace/dams/setup/testlab/CONFIG.xml \
        -p 8101:8888    \
        --name dams_pipe_project \
        dams_prod:<dams_branch_or_latest>_$USER \
        /bin/bash
    ```

3.  to enter the container:
    ```[bash]
    docker exec -it dams_pipe_project bash
    ```

-----------------------------------------

## Example gammasky - host3 - testlab deploy

bootstrap docker image to allow docker to write on host:
    ```[bash]
    ./bootstrap.sh dams_{image}:latest $USER
    ```

Assume to have on host3 a proper gfcl.ini file. You can find it in 
`dams/setup/testlab/gfcl.ini.host3`. in the next command it is mounted
execute from DAMS root:

```[bash]
    cd /path/to/dams/root
    docker run  -it -d \
        -v /archive/GAMMASKY/DL0:/home/gamma/workspace/Data/DL0  \
        -v /archive/GAMMASKY/DL1:/home/gamma/workspace/Data/DL1  \
        -v /archive/GAMMASKY/DL2:/home/gamma/workspace/Data/DL2  \
        -v /archive/GAMMASKY/logs:/home/gamma/workspace/Out/logs \
        -v /archive/GAMMASKY/OutJson:/home/gamma/workspace/Out/json  \
        -v ./setup/testlab/host3/gfcl.ini.host3:/home/gamma/workspace/dams/dl0/gfcl.ini  \
        --entrypoint /home/gamma/workspace/dams/env/entrypoint.sh \
        -e DAMS=/home/gamma/workspace/dams \
        -e RPG_CONFIG=/home/gamma/workspace/dams/setup/testlab \
        -e OSC_CONFIG=/home/gamma/workspace/dams/setup/testlab/CONFIG.xml \
        -p 8101:8888    \
        --name dams_pipe_project --rm \
        dams_prod:<dams_branch_or_latest>_$USER \
        /bin/bash
    ```
