# DAMS
Data Acquisition Modules (DAMS) is a C/Python software used for getting the GAMMA-FLASH data.
High level reconstruction is based on RTA-dataprocessor framework: https://github.com/ASTRO-EDU/rta-dataprocessor.git 

# Usage

Client deployment is done on Main PC is done via docker container. 
Refer to `env/Readme.md` to build a working docker enviroment and create a docker instance. 

It is also necessary to configure the proper enviroment basing on the deployment.
Continue to read section `Client Environment Configuration ` to understand more and know how to configure docker.

# Client Environment Configuration 

Prerequisites:

0. continue reading having a configured docker instance. check `env/Readme.md`

## Server-client (Oscilloscope -> DL0)
1. Define `DAMS` variable in the client machine, pointing to the ROOT of the https://github.com/GAMMA-FLASH/dams repository.
2. Define `DL0DIR` variable pointing to the output directory to store DL0 data. Note: Helper is provided
3. Define `$RPG_CONFIG` variable as the path to the deployment configuration folder.
4. Create a symbolic link "gfcl.ini" for the client configuration:
```
ln -s </path/to/gfcl.machine.ini> $DAMS/dl0/gfcl.ini
```

`$DAMS/setup` folder contains already available deployments, such ad GAMMAFLASH plane payload (gfpl) and a test configuration for GAMMASKY (testlab).

### How to create a new deployment:
1. Create the path to `$RPG_CONFIG`. add a copy of dams/dam/CONFIG.xml to change the Oscilloscope configuration, and create a RPGLIST.cfg file

```
mkdir -p $RPG_CONFIG
cp $DAMS/dam/CONFIG.xml $RPG_CONFIG
touch $RPG_CONFIG/RPGLIST.cfg
```

The `RPGLIST.cfg` file is written by the `$DAMS/setup` scripts to deploy source code on RP servers, start and stop acquisitions
each row entry is a config for a Red Pitaya and must contain the following informations:

```
<rpg_name_x>,<ip address>,<port>,<waveform_number>
```
see GAMMAFLASH as example: `setup/gfpl/RPGLIST.cfg`.

2. edit gfcl.ini file (link) for the client configuration, see $DAMS/setup/gfcl.ini.template as an example.

### influxdb configuration:

influxdb serves as quick look user interface for DAMS project, thanks to its capability to collect and plot time series information on custom dashboards. 
template dashboards can be found in influxdb folder. 

1. influxdb can be started as docker:

```[bash]
docker volume create influx_dams_project_data
docker run -u $(id -u):$(id -g) -d --name influx_dams_project -p xxxx:8086 -v influx_dams_project_data:/var/lib/influxdb2 influxdb:latest
```

2. Enter via browser to influxdb gui and configure user and org. copy and paste token in gfcl.ini config file. create also two buckets to collect point about count rates and housekeeping data.
3. To enable quick look set Enable_Counts and/or Enable_Hk to yes in gfcl.ini file. 
4. import dashboads from json copy pasting the .json inside infludb folder. Edit the queries in the dashboard instances to collect the right points from the configured buckets. points name is generally consistent with rp name present in RPGLIST.cfg

## High level recontruction (DL0 -> DL1 -> DL2)
High level reconstruction must be enabled setting up a suitable RTA-dataprocessor configuration and defining the Output directories.

1. Define `$RTADP_JSON_PATH` as the path to the framework's JSON configuration.
2. Define `DL1DIR` to store DL1 results. Note: Helper is provided
3. Define `DL2DIR` to store DL2 results. Note: Helper is provided

# Server Configuration

## Install and build DAM on server

Pre-requirement: Configure main PC and Red Pitaya such that they are on the same network. SSH server on RP must be enabled and check if the configure DAM port can be used.

1. key installation:
```[bash]
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
ssh-copy-id root@ip
```
2. check connection between docker container and rp manually:
```
ssh root@ip
```
3. from main pc, deploy DAMS source code using the utility:
```
$DAMS/setup/rp/deploy_rp.sh --version <branch_or_tag_name>
```
specific rps from the configured RPGLIST.cfg:
```
$DAMS/setup/rp/deploy_rp.sh --ip 101 --ip 102 --version <branch_or_tag_name>
```

# Run

Refer to `setup/README.md` file


## Jupiter
nohup jupyter-lab --ip="*" --port 8001 --no-browser --autoreload --NotebookApp.token='gf2023#'  --notebook-dir=/home/gamma/workspace --allow-root > jupyterlab_start.log 2>&1 &


## Vscode config 
Copy this config inside `.vscode/` folder to exploit autocompletion:

```
{
    "files.exclude": {
        "**/.idea": true
    }
}
```