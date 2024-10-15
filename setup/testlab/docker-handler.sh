#!/bin/bash
set -e



# Funzione per avviare i container
start_containers() {
  echo "Starting containers..."
  docker start $INFLUX_NAME || echo "$INFLUX_NAME is not running, starting a new instance."
  docker start $GF_NAME || echo "$GF_NAME is not running, starting a new instance."
}

# Funzione per fermare i container
stop_containers() {
  echo "Stopping containers..."
  docker stop $INFLUX_NAME || echo "$INFLUX_NAME is not running."
  docker stop $GF_NAME || echo "$GF_NAME is not running."
}

# Funzione per rimuovere i container
remove_containers() {
  echo "Removing containers..."
  docker rm -f $INFLUX_NAME || echo "$INFLUX_NAME is not running."
  docker rm -f $GF_NAME || echo "$GF_NAME is not running."
}

# Controlla il numero di argomenti
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <start|stop|rm>"
  exit 1
fi

# Carica le variabili di ambiente
source set_env.sh

# Esegui l'azione richiesta
case "$1" in
  start)
    start_containers
    ;;
  stop)
    stop_containers
    ;;
  rm)
    remove_containers
    ;;
  *)
    echo "Invalid option: $1"
    echo "Usage: $0 <start|stop|rm>"
    exit 1
    ;;
esac
