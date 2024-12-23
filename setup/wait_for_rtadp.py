import zmq
import os
import sys
import json
from ConfigurationManager import ConfigurationManager

def listen_and_exit(zmq_endpoint, timeout_s):
    try:
        # Configura il contesto e la socket ZMQ
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect(zmq_endpoint)
        socket.setsockopt_string(zmq.SUBSCRIBE, '')  # Ricevi tutti i messaggi
        socket.setsockopt(zmq.RCVTIMEO, timeout_s*1000)       # Timeout di 1 minuto (60000 ms)

        print(f"Connesso a {zmq_endpoint}. In attesa di messaggi...")
        # Attendi il primo messaggio
       
        started_components = {
            'DL0toDL1-dl0dl1_wm': False,
            'DL1toDL2-dl1dl2_wm': False
        }

        stop = False
        while not stop:
            message = socket.recv_string()
            msg_content = json.loads(message)

            # Check the component from the received message
            pidsource = msg_content['header'].get('pidsource')
            if pidsource in started_components:
                if not started_components[pidsource]:
                    started_components[pidsource] = True
                    print(f"Component {pidsource} started.")

            # Check if all components have been started
            if all(started_components.values()):
                print("All components are started. Exiting...")
                stop = True

            print(f"Messaggio ricevuto: {msg_content}")
            
        

    except zmq.Again:
        # Timeout raggiunto
        print(f"Timeout {timeout_s}s scaduto. Nessun messaggio ricevuto.", file=sys.stderr)
        sys.exit(-1)
    except Exception as e:
        # Per altre eccezioni non previste
        print(f"Errore: {e}", file=sys.stderr)
        sys.exit(-1)
    finally:
        # Pulisci le risorse
        socket.close()
        context.term()

if __name__ == "__main__":
    timeout_s = 10
    if len(sys.argv) < 2:
        print("python wait_for_rtadq.py <config.json> [timeout_s]")
    elif len(sys.argv) == 3 : 
        timeout_s = int(sys.argv[2])
    else: 
        pass

    cfgman = ConfigurationManager(sys.argv[1])
    socketto_san=cfgman.get_configuration("Monitoring")["monitoring_socket"]
    print(socketto_san)
    listen_and_exit(socketto_san, timeout_s)
