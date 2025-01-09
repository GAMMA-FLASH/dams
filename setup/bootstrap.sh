#!/bin/bash
set -e
set +v

log_setup() {
    echo
    log_message "Background execution: ${BACKGROUND}"
    log_message "Starting rpId: ${ATTACHED_NAME}"
    echo
}

# Importa la configurazione comune
source "$(dirname "$0")/common_utils.sh"
cli_argparser $@

# Percorso dello script di bootstrap locale
BOOTSTRAP_RP="$DAMS/setup/gfpl/rp/bootstrapv2-rp.sh"
DEF_USER='root'

bootstrap() {
    local HOST="$2"
    echo -e "\e[32m================ Bootstrapping RPG at addr: $HOST ================\e[0m"
    current_time=$(date -u "+%Y-%m-%d %H:%M:%S")

    if [ ! -f "$BOOTSTRAP_RP" ]; then
        echo "Errore: il file $BOOTSTRAP_RP non esiste."
        exit 1
    fi

    # Leggi il contenuto del file bootstrap
    local SCRIPT_CONTENT=$(<"$BOOTSTRAP_RP")
    echo $SCRIPT_CONTENT
    ssh -tt "${DEF_USER}@${HOST}" << EOF
        date -s '$current_time'
        bash -s << 'REMOTE_SCRIPT'
$SCRIPT_CONTENT
REMOTE_SCRIPT
        exit
EOF
}

# Se è specificato un singolo RPG, logga il messaggio extra
if [ -n "$ATTACHED_NAME" ]; then
    log_message "Bootstrapping only RPG: $ATTACHED_NAME"
fi

process_file_with_function bootstrap
