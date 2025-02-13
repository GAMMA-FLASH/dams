import zmq
import os
import argparse
import sys
import json
from ConfigurationManager import ConfigurationManager

def listen_and_exit(zmq_endpoint, timeout_s, extended_wait=False):
    try:
        # Configura il contesto e la socket ZMQ
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect(zmq_endpoint)
        socket.setsockopt_string(zmq.SUBSCRIBE, '')  # Ricevi tutti i messaggi
        socket.setsockopt(zmq.RCVTIMEO, timeout_s * 1000)  # Timeout in millisecondi

        print(f"Connesso a {zmq_endpoint}. In attesa di messaggi...")

        # Componenti da monitorare
        started_components = {
            'DL0toDL1-dl0dl1_wm': False,
            'DL1toDL2-dl1dl2_wm': False
        }

        # Se extended_wait è True, aggiungi altri due componenti
        if extended_wait:
            started_components.update({
                'DL0toDL2-dl0dl2_wm': False,
                'DL2Checker-dl2ccheck_wm': False
            })

        stop = False
        while not stop:
            try:
                message = socket.recv_string()
                msg_content = json.loads(message)

                # Controlla il componente ricevuto
                pidsource = msg_content['header'].get('pidsource')
                if pidsource in started_components:
                    if not started_components[pidsource]:
                        started_components[pidsource] = True
                        print(f"Component {pidsource} started.")

                # Controlla se tutti i componenti attesi sono stati avviati
                if all(started_components.values()):
                    print("All components are started. Exiting...")
                    stop = True

                print(f"Messaggio ricevuto: {msg_content}")

            except zmq.Again:
                # Timeout di ricezione
                print(f"Timeout {timeout_s}s scaduto. Nessun messaggio ricevuto.", file=sys.stderr)
                sys.exit(-1)

    except Exception as e:
        print(f"Errore: {e}", file=sys.stderr)
        sys.exit(-1)
    finally:
        # Pulizia delle risorse
        socket.close()
        context.term()

def main():
    # Configura il parser degli argomenti
    parser = argparse.ArgumentParser(description="Attende la connessione al socket RTADQ")
    parser.add_argument("config", type=str, help="Percorso al file di configurazione (config.json)")
    parser.add_argument("timeout", type=int, nargs="?", default=10, help="Timeout in secondi (default: 10)")
    parser.add_argument("--extended", action="store_true", help="Abilita la modalità di attesa estesa")

    # Parsing degli argomenti
    args = parser.parse_args()

    # Carica la configurazione
    cfgman = ConfigurationManager(args.config)
    socketto_san = cfgman.get_configuration("Monitoring")["monitoring_socket"]
    print(f"Socket: {socketto_san}")

    # Avvia l'ascolto
    print(f"Connection to {socketto_san} with timeout {args.timeout} {'extended mode' if args.extended else ''}")
    listen_and_exit(socketto_san, args.timeout, args.extended)

if __name__ == "__main__":
    main()