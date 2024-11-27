#!/bin/bash
set -v

export PROJECT=gammasky

export INFLUX_NAME="influx_${PROJECT}"
export INFLUX_IMAGE="influxdb:latest"
export GF_NAME="gf_${PROJECT}"
export GF_IMAGE="gammaflash:1.5.0_${USER}"

export INFLUX_DATA="/data01/archive/gammasky/influx/data"


set +v