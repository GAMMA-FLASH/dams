#!/bin/bash

cd ~
source ./entrypoint.sh
cd /home/worker/workspace/testgammaflash/dams/pipe/env
source ./exports_pythonpath.sh
echo $PYTHONPATH
cd ..