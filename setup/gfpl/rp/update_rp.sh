#!/bin/bash


if [ -n "$1" ]; then 
 	BRANCH=$1
else
	echo "branch not defined"
	exit
fi 

echo "RP Update utility called"
echo "deploying branch $BRANCH"

REPO_DIR="/root/workspace/dams/"
DAM_DIR="/root/workspace/dams/dam"
REPO_URL="https://github.com/GAMMA-FLASH/dams.git"  


if [ ! -d "$REPO_DIR/.git" ]; then
    echo "Repository non trovato. Clonazione in corso..."
    mkdir -p "$REPO_DIR" 
    git clone "$REPO_URL" "$REPO_DIR"
fi

cd "$DAM_DIR" || { echo "Impossibile accedere alla directory $DAM_DIR"; exit 1; }

git clean -fdx
git fetch
git checkout "$BRANCH"
git pull origin "$BRANCH"
make

