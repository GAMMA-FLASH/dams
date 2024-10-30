#!/bin/bash

# Importa la configurazione comune
source "$(dirname "$0")/.common"
echo 
# Percorso dello script di bootstrap da copiare ed eseguire sui Red Pitaya
BOOTSTRAP_RP="bootstrap2.sh"
DEF_USER='root'

bootstrap() {
    local HOST="$1"
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
# Esegui il bootstrap su ogni RPG presente nel file di configurazione
while IFS=',' read -r rp_name addr port wformno  || [[ -n "$rp_name" ]]; do
    if [ -z "$ATTACHED_NAME" ] || [ "$ATTACHED_NAME" = "$rp_name" ]; then
        bootstrap "$addr"
        # Se è stato specificato un solo RPG, esci dopo averlo avviato
        [ -n "$ATTACHED_NAME" ] && exit 0
    fi
done < "$RPG_CONFIG"
