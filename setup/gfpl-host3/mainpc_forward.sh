#!/bin/bash

# Controllo degli argomenti
if [ "$#" -ne 5 ]; then
    echo "Uso: $0 <add|delete> <IPCLIENT> <IPRP> <DAM_RP_PORT> <DAM_FW_PORT> <INTERFACE>"
    echo "Esempio: $0 add 192.168.1.10 192.168.1.20 1234 5678 "
    exit 1
fi

# Variabili passate dalla riga di comando
ACTION=$1
IPCLIENT=$2
IPRP=$3
DAM_RP_PORT=$4
DAM_FW_PORT=$5

# Funzione per abilitare il forwarding temporaneo
# enable_packet_forwarding() {
#     echo "[INFO] Abilitazione temporanea del forwarding dei pacchetti..."
#     sudo sysctl -w net.ipv4.ip_forward=1
# }

# Funzione per disabilitare il forwarding temporaneo
# disable_packet_forwarding() {
#     echo "[INFO] Disabilitazione del forwarding dei pacchetti..."
#     sudo sysctl -w net.ipv4.ip_forward=0
# }

# Funzione per aggiungere regole iptables
add_iptables_rules() {
    echo "[INFO] Aggiunta delle regole iptables..."
    echo "[LOG] Forwarding: Porta $DAM_FW_PORT -> $IPRP:$DAM_RP_PORT"
    sudo iptables -t nat -A PREROUTING -p tcp --dport $DAM_FW_PORT -j DNAT --to-destination $IPRP:$DAM_RP_PORT
    
    echo "[LOG] Accettazione traffico verso $IPRP sulla porta $DAM_RP_PORT"
    sudo iptables -A FORWARD -p tcp -d $IPRP --dport $DAM_RP_PORT -j ACCEPT
    
    echo "[LOG] Apertura connessioni da $IPCLIENT verso la porta $DAM_FW_PORT"
    sudo iptables -A INPUT -p tcp --dport $DAM_FW_PORT -s $IPCLIENT -j ACCEPT
    sudo iptables -A OUTPUT -p tcp --dport $DAM_FW_PORT -d $IPCLIENT -j ACCEPT
}

# Funzione per rimuovere regole iptables
delete_iptables_rules() {
    echo "[INFO] Rimozione delle regole iptables..."
    echo "[LOG] Rimozione Forwarding: Porta $DAM_FW_PORT -> $IPRP:$DAM_RP_PORT"
    sudo iptables -t nat -D PREROUTING -p tcp --dport $DAM_FW_PORT -j DNAT --to-destination $IPRP:$DAM_RP_PORT
    
    echo "[LOG] Rimozione regola di accettazione traffico verso $IPRP sulla porta $DAM_RP_PORT"
    sudo iptables -D FORWARD -p tcp -d $IPRP --dport $DAM_RP_PORT -j ACCEPT
    
    echo "[LOG] Rimozione apertura connessioni da $IPCLIENT verso la porta $DAM_FW_PORT"
    sudo iptables -D INPUT -p tcp --dport $DAM_FW_PORT -s $IPCLIENT -j ACCEPT
    sudo iptables -D OUTPUT -p tcp --dport $DAM_FW_PORT -d $IPCLIENT -j ACCEPT
}

# Stampa parametri inseriti
echo "[INFO] Parametri inseriti:"
echo "  Azione: $ACTION"
echo "  IPCLIENT: $IPCLIENT"
echo "  IPRP: $IPRP"
echo "  Porta DAM destinatario (RP): $DAM_RP_PORT"
echo "  Porta DAM forwardata: $DAM_FW_PORT"

# Eseguire azione
case "$ACTION" in
    add)
        echo "[INFO] Esecuzione configurazione 'add'"
        # enable_packet_forwarding
        add_iptables_rules
        echo "[INFO] Configurazione aggiunta con successo."
        ;;
    delete)
        echo "[INFO] Esecuzione configurazione 'delete'"
        delete_iptables_rules
        # disable_packet_forwarding
        echo "[INFO] Configurazione rimossa con successo."
        ;;
    *)
        echo "[ERROR] Argomento non valido. Usa 'add' o 'delete'."
        exit 1
        ;;
esac

# Mostra le regole attuali per controllo
echo "[INFO] Regole attuali (iptables):"
sudo iptables -L -v -n
echo "[INFO] Regole attuali (iptables NAT):"
sudo iptables -t nat -L -v -n

