# How to use DAMS

## set env vars

`DAMS` is the folder pointing to the dams repository root folder.
`RPG_CONFIG` is the path to folder or to configuration file `RPGLIST.cfg` of a deployment setup.
`DL0DIR` is the DL0 output folder for the current observation.
`DL1DIR` is the DL1 output folder for the current observation.
`DL2DIR` is the DL2 output folder for the current observation.

you can find the helper script: `setup/output_directories.sh` to rapid setup all the vars:
```[bash]
source $DAMS/setup/output_directories.sh /common/base/path
```
## Configuration

the following steps refer to a proper configured enviroment.
Refer to `README.md, sec. 'Client Environment Configuration'` to setup the environment


## setup current time on main computer

```
date -s YYYY-MM-DD HH:mm:SS
```
example to set date and time to 6th august 2024 at 13:24:50
```
date -s 2024-08-06 13:24:50
```

## deployment configuration
deployment configuration are inside `setup/<deployment_name>` folder.
`RPGLIST.cfg` is the file used from start.sh utility to start all gammaflash client for each RedPitaya.
RPG List contains one line for each Red Pitaya with the following informations:
```
<rpg_name_x>,<ip address>,<port>,<waveform_number>
```
for gfcl, RPID is (101-106)
for testlab, RPID is SIPM

## execute bootstrap

```
cd $DAMS/setup/ && ./bootstrap.sh
```

## start the acquisition with rtadp DL0-DL2


To start all clients and DL0-DL1-DL2 production:
1. Check the rtadp configuration. `README.md, subsec. High level recontruction (DL0 -> DL1 -> DL2)`
2. Check the gfcl.ini configuration contains "enable yes" in DL0DL2_PIPE section. 
3. execute:
```
$DAMS/setup/start.sh -r
```
further options described in helper
1. To start all clients with multiprocessing capability:
```
$DAMS/setup/start.sh -m
```
N.B. rtadp basic logs will be in `$DAMS/logs/`


To start just one client, attached to shell:
```
$DAMS/setup/start.sh -a -i <RPGNAME>
```


## start the acquisition

To stop all clients:
```
$DAMS/setup/stop_clients.sh
```

To stop just one client specify the RPGNAME
```
$DAMS/setup/stop_clients.sh -i <RPGNAME>
```