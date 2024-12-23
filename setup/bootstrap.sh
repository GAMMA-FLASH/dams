#!/bin/bash

# Importa la configurazione comune
source "$(dirname "$0")/.common"
# Percorso dello script di bootstrap da copiare ed eseguire sui Red Pitaya
BOOTSTRAP_RP="bootstrap2.sh"
DEF_USER='root'

bootstrap() {
    local HOST="$2"
    echo -e "\e[32m================ Bootstrapping RPG at addr: $HOST ================\e[0m"
    current_time=$(date -u "+%Y-%m-%d %H:%M:%S")
    ssh -tt "${DEF_USER}@${HOST}" << EOF
        date -s '$current_time'
        bash $BOOTSTRAP_RP
        exit
EOF
}
# Se è specificato un singolo RPG, logga il messaggio extra
if [ -n "$ATTACHED_NAME" ]; then
    log_message "Bootstrapping only RPG: $ATTACHED_NAME"
fi

process_file_with_function bootstrap