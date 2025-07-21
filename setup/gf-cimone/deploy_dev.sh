#!/bin/bash

# docker pull git.ia2.inaf.it:5050/gammasky/gammasky-cimone/dams_base:1.6.0

#/home/laboratorio/workspace/dams/env/bootstrap.sh gammaflash:1.5.0 $USER

# Ottieni la directory dello script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Spostati nella directory dello script
cd "$SCRIPT_DIR"

# Trova la root del repository Git risalendo la gerarchia
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

if [ $? -ne 0 ]; then
  echo "Errore: la directory corrente o i suoi genitori non sono dentro un repository Git."
  exit 1
fi
DAMS_BASENAME="dams_gammaflash"
# Verifica che il nome della directory root sia 'dams'
if [ "$(basename "$REPO_ROOT")" != $DAMS_BASENAME ]; then
  echo "Errore: la root del repository non si chiama '$DAMS_BASENAME'."
  echo "Root trovata: $REPO_ROOT"
  exit 2
fi

echo "La root del repository 'dams' è: $REPO_ROOT"

docker run -it -d \
  -v /data/archive/GAMMAFLASH:/home/usergamma/workspace/Data \
  -v $REPO_ROOT:/home/usergamma/workspace/dams \
  -v /data/archive/GAMMASKY/OutJson/:/home/usergamma/workspace/Data/Out \
  -v $REPO_ROOT/setup/gf-cimone/maincomputer/gfcl.ini.maincomputer:/home/usergamma/workspace/dams/dl0/gfcl.ini \
  -v $HOME/.ssh:/home/usergamma/.ssh \
  -e DAMS=/home/usergamma/workspace/dams \
  -w /home/usergamma/workspace/dams \
  --init \
  --add-host gf101.gammaflash:192.168.1.101 \
  --add-host gf102.gammaflash:192.168.1.102 \
  --add-host gf103.gammaflash:192.168.1.103 \
  --add-host gf104.gammaflash:192.168.1.104 \
  --add-host gf105.gammaflash:192.168.1.105 \
  --add-host gf106.gammaflash:192.168.1.106 \
  --name dams_gf \
  git.ia2.inaf.it:5050/gammasky/gammasky-cimone/dams_base:1.5.1_$USER tail -f /dev/null
