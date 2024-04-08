# DAMS
Data Acquisition Modules (DAMS) is a C/Python software used for getting the GAMMA-FLASH data.

## Run

To run the acquisition 
```
python gfcl.py --rp_ip X.X.X.X --rp_port Y --rp_id Z --outdir "outdir" --nwfs 10000
```

## Jupiter
nohup jupyter-lab --ip="*" --port 8001 --no-browser --autoreload --NotebookApp.token='gf2023#'  --notebook-dir=/home/usergamma/workspace --allow-root > jupyterlab_start.log 2>&1 &
