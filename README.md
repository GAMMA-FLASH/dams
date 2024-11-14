# DAMS
Data Acquisition Modules (DAMS) is a C/Python software used for getting the GAMMA-FLASH data.

# Client Enviroment
define DAMS variable in the client machine, pointing to the ROOT of the https://github.com/GAMMA-FLASH/dams repository
to store data, define "ODIR" variable pointing to the output directory 

## Install dam software on RP
Manually clone the source code in RP. assume them connected to network
```
ssh rp_ip 
cd /root/workspace
git clone https://github.com/GAMMA-FLASH/dams
```
### Build dam:

2 alternatives:

inside rp:
```
ssh `rp`
/root/workspace/dams/setup/rp/update_rp.sh <branch_name>
```
from client, multiple build:
from 101 to 106
```
$DAMS/setup/rp/deploy_rp.sh --ip all --version <branch_or_tag_name>
```
specific rp:
```
$DAMS/setup/rp/deploy_rp.sh --ip 101 --ip 102 --version <branch_or_tag_name>

```

## Run

To run the acquisition 
```
python gfcl.py --rp_ip X.X.X.X --rp_port Y --rp_id Z --outdir "outdir" --nwfs 10000
```
or define ODIR variable
```

```


## Jupiter
nohup jupyter-lab --ip="*" --port 8001 --no-browser --autoreload --NotebookApp.token='gf2023#'  --notebook-dir=/home/usergamma/workspace --allow-root > jupyterlab_start.log 2>&1 &


## Vscode config 
Copy this config inside `.vscode/` folder to exploit autocompletion:

```
{
    "files.exclude": {
        "**/.idea": true
    }
}
```