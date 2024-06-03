import zmq
import json
import time
import sys
import os
from printcolors import colore_verde, reset_colore


def publish(path_dl2: str, socket: zmq.Socket, F_sleep: bool, time_sleep_inframessage: int):
    if not os.path.exists(path_dl2):
        print(f"WARNING! path_dl2 \"{path_dl2}\" does not exists!")
        sys.exit(1)
    # BASE CASE: path_dl2 is a file
    if not os.path.isdir(path_dl2):
        if not ('.ok' == os.path.splitext(path_dl2)[-1]):
            # Sleep only first time for 
            if F_sleep: time.sleep(1)
            time.sleep(time_sleep_inframessage)
            socket.send_string(path_dl2)
            print(f"Sent: {colore_verde}{os.path.basename(path_dl2)}{reset_colore}")
    # INDUCTIVE CASE: path_dl2 is a directory
    else:
        # List children for path_dl2
        children = os.listdir(path_dl2)
        for child in children:
            # Combine new path
            new__path_dl2 = os.path.join(path_dl2, child)
            # Publish each new child
            time.sleep(time_sleep_inframessage)
            publish(new__path_dl2, socket, F_sleep, time_sleep_inframessage)
            # Change sleep status
            F_sleep = F_sleep and False


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python dl0_publisher.py <path/to/dl2_data/> <socket>"
              "<time_sleep>")
        sys.exit(1)
    # Get the DL2 data path
    path_dl2 = sys.argv[1] 
    # Get the socket name where publishing the file name to check DL2
    socketstring = sys.argv[2]
    for i in range(3):
        print(f"{3-i}")
        time.sleep(1)
    time_sleep_inframessage = int(sys.argv[3])
    # Establish connection
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(socketstring)
    publish(path_dl2, socket, True, time_sleep_inframessage)