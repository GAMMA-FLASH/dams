#!/bin/bash

if [ -n $1 ]; then 
 	BRANCH=$1
 else
	BRANCH=$(git symbolic-ref --short HEAD)
fi 
cd /root/workspace/dams/dam
if [  $(basename `git rev-parse --show-toplevel`) == "dams" ]; then
	git clean -fdx
        git checkout $BRANCH
	git pull origin $BRANCH
       	make
else
 echo "Not dams repository"
 exit -1
fi 
	

