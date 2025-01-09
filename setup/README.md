# How to use DAMS

## set env vars

`DAMS` is the folder pointing to the dams repository root folder.
`RPG_CONFIG` is the path to folder or to configuration file `RPGLIST.cfg` of a deployment setup
`DL0DIR` is the DL0 and DL2 output folder for the current obervation.

## create a symbolic link to gammaflash client configuration .ini file

```
ln -s </path/to/gfcl.machine.ini> $DAMS/dl0/gfcl.ini
```

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
RPG List contains one line for each Red Pitaya, with the following informations:
```
<rpg_name_x>,<ip address>,<port>,<waveform_number>
```
for gfcl, RPID is (101-106)
for testlab, RPID is SIPM

## execute bootstrap
install `bootstrap2-rp.sh` in all red pitaya:
```
scp $DAMS/setup/gfpl/rp/bootstrap2-rp.sh root@rp_ip:/root/bootstrap2.sh
```
execute:
```
cd $DAMS/setup/ && ./bootstrap.sh
```

## start the acquisition

To start all clients:
```
$DAMS/setup/start.sh 
```
make sure all envvars are defined

N.B. logs will be in `$DAMS/logs/dl0`


To start just one client:
```
$DAMS/setup/start.sh --config $DAMS/setup/<deployment_name> -a <RPGNAME>
```


## start the acquisition

To stop all clients:
```
$DAMS/setup/stop_clients.sh
```

To stop just one client specify the RPGNAME
```
$DAMS/setup/stop_clients.sh -a <RPGNAME>
```