#!/bin/bash

echo "Input envvars:"
echo "DAMS: $DAMS"
echo "RPG_CONFIG: $RPG_CONFIG"

# Nome del vecchio e del nuovo ambiente
condaenviron="gammaenv"
cd $HOME
echo "starting gammasky-container"
source activate $condaenviron




TOKEN="${TOKEN:-gf2023#}"


echo "starting notebook. Use Token: $TOKEN"
# Avviare il notebook Jupyter, legandolo a tutte le interfacce di rete e mettendo i log su stdout
jupyter-lab --ip="*" --no-browser --autoreload --NotebookApp.token="$TOKEN" --notebook-dir=/home/gamma/workspace/dams --allow-root > /dev/stdout 2>&1 &

# Verifica se le variabili sono già presenti
if ! grep -q "export DAMS=" ~/.bashrc; then
    echo "exporting variables"
    echo "export DAMS=${DAMS:-/home/gamma/workspace/dams}" >> ~/.bashrc
    echo "export RPG_CONFIG=${RPG_CONFIG:-$DAMS/setup/testlab}" >> ~/.bashrc
    echo "export RTADP_JSON_PATH=${RTADP_JSON_PATH:-/home/gamma/workspace/dams/pipe/config.json}" >> ~/.bashrc
    echo "export CONDA_ENV_NAME=${CONDA_ENV_NAME:-$condaenviron}" >> ~/.bashrc
else
    echo "Le variabili di ambiente sono già presenti in .bashrc."
fi

# Mantieni il container in esecuzione (per evitare che termini subito)
echo "Done"
tail -f /dev/null

