#!/bin/bash

# Nome del vecchio e del nuovo ambiente
condaenviron="gammaflash"
cd $HOME
echo "starting gammasky-container"
source activate $condaenviron

#!/bin/bash

TOKEN="gf2023#"

echo "starting notebook. Use Token: $TOKEN"
# Avviare il notebook Jupyter, legandolo a tutte le interfacce di rete e mettendo i log su stdout
nohup jupyter-lab --ip="*" --no-browser --autoreload --NotebookApp.token="$TOKEN" --notebook-dir=/home/usergamma/dams --allow-root > /dev/stdout 2>&1 &

# Verifica se le variabili sono già presenti
if ! grep -q "export DAMS=" ~/.bashrc; then
    echo "exporting variables"
    echo 'export DAMS="/home/usergamma/dams"' >> ~/.bashrc
    echo 'export RPG_CONFIG="$DAMS/setup/testlab"' >> ~/.bashrc
else
    echo "Le variabili di ambiente sono già presenti in .bashrc."
fi

# Mantieni il container in esecuzione (per evitare che termini subito)
echo "Done"
tail -f /dev/null

