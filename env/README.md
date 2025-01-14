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

* Build the images using docker compose:
  
```[bash]
docker compose build
```

it will build base and prod image.

`base` image hase no source code, it must be mounted from host

`prod` image comes with source code and testlab setup installed. Note: check setup

## entrypoint with Jupyter start

Starts Jupyter in the entrypoint and defines in bashrc the envvars DAMS, RPG_CONFIG. 

bootstrap docker image to allow docker to write on host:

```[bash]
./bootstrap.sh dams_{image}:latest $USER
```

mount all the archives you need to write data and logs:

bond a port for opening Jupyter notebook

```[bash]
docker run  -it -d \
    -v /archive/.../DL0:/home/gamma/workspace/Data/DL0  \
    -v /archive/.../DL1:/home/gamma/workspace/Data/DL1  \
    -v /archive/.../DL2:/home/gamma/workspace/Data/DL2  \
    -v /archive/.../logs:/home/gamma/workspace/Out/logs \
    -v /archive/.../OutJson:/home/gamma/workspace/Out/json  \
    -v /path/to/.../dams:/home/gamma/workspace/dams \  ###NOTE: do not mount with prod image
    --entrypoint /home/gamma/workspace/dams/env/entrypoint.sh \
    -e DAMS=/home/gamma/workspace/dams \
    -e RPG_CONFIG=/home/gamma/workspace/dams/setup/testlab \
    -p 8101:8888    \
    --name dams_pipe_project \
    dams_image:latest_$USER \
    /bin/bash
```

to enter the container:

```[bash]
docker exec -it dams_pipe_project bash
```
-----------------------------------------
