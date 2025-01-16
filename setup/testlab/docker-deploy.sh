#!/bin/bash
set -e 

source set_env.sh

cd $(dirname $0)

echo Setting up $INFLUX_NAME container with image: $INFLUX_IMAGE
docker run -u $(id -u):$(id -g) -d --name $INFLUX_NAME -p 7804:8086 -v $INFLUX_DATA:/var/lib/influxdb2 $INFLUX_IMAGE

echo Setting up $GF_NAME container with image: $GF_IMAGE
export DATA01="/data01/archive/gammasky/data"
export DATA02="/data02/"
echo Data01 is $DATA01
echo Data02 is $DATA02
docker run -it -d \
    -v $DATA01:/home/gamma/workspace \
    -v $DATA01:/home/gamma/workspace \
    -v $DATA02:/data02/ \
    -v /home/gammasky/dams:/home/gamma/workspace/dams \
    -e DAMS=/home/gamma/workspace/dams  \
    -p 7805:8888 \
    --name $GF_NAME \
    gammaflash:1.5.0_${USER} \
    /bin/bash