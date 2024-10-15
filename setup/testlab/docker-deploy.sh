#!/bin/bash
set -e 

source set_env.sh

echo Setting up $INFLUX_NAME container with image: $INFLUX_IMAGE
docker run -u $(id -u):$(id -g) -d --name $INFLUX_NAME -p 7804:8086 -v $INFLUX_DATA:/var/lib/influxdb2 $INFLUX_IMAGE

echo Setting up $GF_NAME container with image: $GF_IMAGE
echo Data01 is $DATA01
echo Data02 is $DATA02
docker run -it -d -v $DATA01:/home/usergamma/workspace -v $DATA02:/data02/ -v /home/gammasky/dams:/home/usergamma/workspace/dams -e DAMS=/home/usergamma/workspace/dams  -p 7805:8888 --name $GF_NAME gammaflash:1.5.0_${USER} /bin/bash