import zmq
import sys

colore_rosa = '\033[95m'
colore_ciano = '\033[96m'
colore_verde = '\033[92m'
colore_giallo = '\033[93m'
colore_rosso = '\033[91m'
reset_colore = '\033[0m'

def main(socketstring):
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(socketstring)
    # Setta il prefisso del filtro dei messaggi, può essere una stringa vuota per ricevere tutto
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
    F_esc = True
    while F_esc:
        try:
            message = subscriber.recv_string()
            print(f"Received: {colore_verde}{message}{reset_colore}")
        except KeyboardInterrupt:
            F_esc = False
            print()
            print("Quitting sniffer...")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: zmq_subscriber.py <socket>")
        sys.exit(1)
    socketstring = sys.argv[1]
    main(socketstring)