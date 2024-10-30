#!/bin/bash

PIDS=gfcl.pids
DL0_LOGS=$DAMS/logs/dl0
CONDA_ENV_NAME="gammaflash"

# Funzione per mostrare l'uso dello script
usage() {
    echo "Usage: $0 [--config <RPG_config_or_directory>] [--background] [--attached [RPGNAME]] [--multiprocessing]"
    exit 1
}

# Inizializza variabili
BACKGROUND=true
ATTACHED_NAME=""
MULTIPROCESSING=""

# Se RPG_CONFIG è già definito come variabile d'ambiente, usala come valore predefinito
# Controllo che RPG_CONFIG sia stato definito, o se esiste già nella variabile d'ambiente

RPG_CONFIG="${RPG_CONFIG:-}"

# Parsing degli argomenti della riga di comando
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --config|-c)
            RPG_CONFIG="$2"
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

# Controllo che RPG_CONFIG sia stato definito, o se esiste già nella variabile d'ambiente
if [ -z "$RPG_CONFIG" ]; then
    echo "RPG_CONFIG not defined. Please set it as an environment variable or use --config."
    usage
    exit 1
fi
RPG_DEFAULT_FILE="RPGLIST.cfg"
if [ -d "$RPG_CONFIG" ]; then
    # Se è una directory, controlla se il file di configurazione predefinito esiste
    if [ -e "$RPG_CONFIG/$RPG_DEFAULT_FILE" ]; then
        RPG_CONFIG="$RPG_CONFIG/$RPG_DEFAULT_FILE"
    else
        echo "Default config file $RPG_DEFAULT_FILE not found in directory $RPG_CONFIG."
        exit 1
    fi
fi
# Risolvi il percorso assoluto per RPG_CONFIG
RPG_CONFIG=$(readlink -f "$RPG_CONFIG")

echo -e "\033[0;32m -- Using Red Pitaya deployment configuration: $RPG_CONFIG\033[0m"

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
echo -e "\033[0;32m -- Using Client Script: ${GFCL}\033[0m"

cd "$DAMS/dl0" || exit

# Check if gfcl.ini exists
if [ -e "gfcl.ini" ]; then

    echo -e "\033[0;32m -- Using Gammaflash Client configuration: $(readlink -f gfcl.ini)\033[0m"
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
while IFS=',' read -r rp_name addr port wformno || [[ -n "$addr" ]]; do
    # Memorizza il primo RPG
    if [ -z "$FIRST_RPG_NAME" ]; then
        FIRST_RPG_NAME="$rp_name"
    fi

    # Creazione della directory di output
    mkdir -p "$ODIR/$rp_name/35mV/"
    
    # Esecuzione del comando con i parametri letti
    if [ "$BACKGROUND" = true ]; then
        # Lancia in background
        nohup $PYTHON $GFCL --addr "$addr" --port "$port" --outdir "$ODIR/$rp_name/35mV/" --wformno "$wformno" $MULTIPROCESSING > "$DL0_LOGS/gfcl_$rp_name.log" 2>&1 &
    elif [ "$ATTACHED_NAME" = "$rp_name" ] || ( [ -z "$ATTACHED_NAME" ] && [ "$rp_name" = "$FIRST_RPG_NAME" ] ); then
        # Lancia in foreground se corrisponde il nome o se ATTACHED_NAME è vuoto e corrisponde al primo RPG
        echo "Launched RPG: $rp_name"
        $PYTHON $GFCL --addr "$addr" --port "$port" --outdir "$ODIR/$rp_name/35mV/" --wformno "$wformno" $MULTIPROCESSING
        exit 0 # Esci dopo aver lanciato l'attached process
    fi
done < "$RPG_CONFIG"

# Se in background, esegui tutti i processi
if [ "$BACKGROUND" = true ]; then
    echo "All processes launched in background."
fi
