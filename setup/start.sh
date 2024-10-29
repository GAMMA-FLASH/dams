#!/bin/bash

PIDS=gfcl.pids
DL0_LOGS=$DAMS/logs/dl0
CONDA_ENV_NAME="gammaflash"
CONFIG_FILE_NAME_DEF="RPGLIST.cfg"

# Funzione per mostrare l'uso dello script
usage() {
    echo "Usage: $0 --config <config_file_or_directory> [--background] [--attached [RPGNAME]] [--multiprocessing]"
    exit 1
}

# Inizializza variabili
CONFIG_FILE=""
BACKGROUND=true
ATTACHED_NAME=""
MULTIPROCESSING=""

# Parsing degli argomenti della riga di comando
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --config|-c)
            if [ -d "$2" ]; then
                # Se è una directory, controlla se il file di configurazione predefinito esiste
                if [ -e "$2/$CONFIG_FILE_NAME_DEF" ]; then
                    CONFIG_FILE="$2/$CONFIG_FILE_NAME_DEF"
                else
                    echo "Default config file $CONFIG_FILE_NAME_DEF not found in directory $2."
                    exit 1
                fi
            else
                CONFIG_FILE="$2"
            fi
            shift ;;
        --background|-b) BACKGROUND=true ;;
        --attached|-a)
            BACKGROUND=false
            ATTACHED_NAME="$2"
            if [ -z "$ATTACHED_NAME" ]; then
                # Se ATTACHED_NAME è vuoto, impostalo al primo RPG della lista
                ATTACHED_NAME=""
            fi
            shift ;;
        --multiprocessing|-m) MULTIPROCESSING="--multiprocessing" ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

# Controllo che CONFIG_FILE sia stato definito
if [ -z "$CONFIG_FILE" ]; then
    echo "CONFIG_FILE not defined"
    usage
fi

# Risolvi il percorso assoluto per CONFIG_FILE
CONFIG_FILE=$(readlink -f "$CONFIG_FILE")

# Check if ODIR is defined
if [ -z "$ODIR" ]; then
    echo "ODIR not defined"
    exit 1
fi

# Check if DAMS is defined
if [ -z "$DAMS" ]; then
    echo "DAMS root not defined"
    exit 1
fi

mkdir -p "$DL0_LOGS"

GFCL=${GFCL:-"$DAMS/dl0/gfcl.py"}
echo "Using Client Script: ${GFCL}"

cd "$DAMS/dl0" || exit

# Check if gfcl.ini exists
if [ -e "gfcl.ini" ]; then
    echo "Using gfcl.ini: $(readlink -f gfcl.ini)"
else
    echo "gfcl.ini not defined"
    exit 1
fi

if [ "$(cat /etc/hostname)" = "gamma-flash.iasfbo.inaf.it" ]; then
    PYTHON=python3.9
else
    source activate "$CONDA_ENV_NAME"
    PYTHON=python
fi

# Variabile per tenere traccia del primo RPG
FIRST_RPG_NAME=""

# Itera su ogni riga del file di configurazione
while IFS=',' read -r addr port wformno dir_name; do
    # Memorizza il primo RPG
    if [ -z "$FIRST_RPG_NAME" ]; then
        FIRST_RPG_NAME="$dir_name"
    fi

    # Creazione della directory di output
    mkdir -p "$ODIR/$dir_name/35mV/"
    
    # Esecuzione del comando con i parametri letti
    if [ "$BACKGROUND" = true ]; then
        # Lancia in background
        echo "nohup $PYTHON $GFCL --addr \"$addr\" --port \"$port\" --outdir \"$ODIR/$dir_name/35mV/\" --wformno \"$wformno\" $MULTIPROCESSING > \"$DL0_LOGS/gfcl_$dir_name.log\" &"
    elif [ "$ATTACHED_NAME" = "$dir_name" ] || ( [ -z "$ATTACHED_NAME" ] && [ "$dir_name" = "$FIRST_RPG_NAME" ] ); then
        # Lancia in foreground se corrisponde il nome o se ATTACHED_NAME è vuoto e corrisponde al primo RPG
        echo "$PYTHON $GFCL --addr \"$addr\" --port \"$port\" --outdir \"$ODIR/$dir_name/35mV/\" --wformno \"$wformno\" $MULTIPROCESSING"
        $PYTHON $GFCL --addr "$addr" --port "$port" --outdir "$ODIR/$dir_name/35mV/" --wformno "$wformno" $MULTIPROCESSING
        echo "Launched RPG: $dir_name"
        exit 0 # Esci dopo aver lanciato l'attached process
    fi
done < "$CONFIG_FILE"

# Se in background, esegui tutti i processi
if [ "$BACKGROUND" = true ]; then
    echo "All processes launched in background."
fi
