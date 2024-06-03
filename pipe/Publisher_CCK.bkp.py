import zmq
import json
import time
import sys
import os
from printcolors import colore_verde, reset_colore

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python dl0_publisher.py <path/to/dl2_data/> <socket>")
        sys.exit(1)
    # Get the DL2 data path
    path_dl2 = sys.argv[1] 
    # Get the socket name where publishing the file name to check DL2
    socketstring = sys.argv[2]
    for i in range(3):
        print(f"{3-i}")
        time.sleep(1)
    #
    print(path_dl2)
    list_fileDL2 = os.listdir(path_dl2)
    print(list_fileDL2)
    list_fileDL2 = list(filter(lambda f: '.dl2.h5' in f, list_fileDL2))
    print(list_fileDL2)
    # Establish connection
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(socketstring)
    F_sleep = True
    for filename in list_fileDL2:
        if F_sleep:
            time.sleep(1)
            F_sleep = False
        socket.send_string(
            os.path.join(path_dl2, filename))
        print(f"Sent: {colore_verde}{filename}{reset_colore}")
