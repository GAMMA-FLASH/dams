import zmq
import json
import time
import sys
import os

from printcolors import colore_verde, reset_colore, colore_giallo



def publish(path_dl0: str, 
            path_dl1: str, 
            path_dl2: str, 
            F_sleep: bool, 
            socket: zmq.Socket,
            time_sleep_inframessage: int):
    if not os.path.exists(path_dl0):
        print(f"WARNING! path_dl0 \"{path_dl0}\" does not exists!")
        return
    # BASE CASE: path_dl0 is a file
    if not os.path.isdir(path_dl0):
        if not ('.ok' == os.path.splitext(path_dl0)[-1]):
            # Sleep only first time for 
            if F_sleep: time.sleep(1)
            # Data message creation
            # data = {"path_dl0_folder": os.path.dirname(path_dl0), 
            #         "path_dl1_folder": os.path.dirname(path_dl1), 
            #         "path_dl2_folder": os.path.dirname(path_dl2), 
            #         "filename":        os.path.basename(path_dl0)}
            data = {"path_dl0_folder": os.path.dirname(path_dl0), 
                    "path_dl1_folder": os.path.dirname(path_dl1), 
                    "path_dl2_folder": os.path.dirname(path_dl2), 
                    "filename":        os.path.basename(path_dl0)}
            # Dump message
            message = json.dumps(data)
            # Send message
            socket.send_string(message)
            # Update the user
            print(f"Sent: {colore_verde}{message}{reset_colore}")
        else:
            print(f"skip: {colore_giallo}{path_dl0}{reset_colore}")
    # INDUCTIVE CASE: path_dl0 is a directory
    else:
        # Create the directory
        os.makedirs(path_dl1, exist_ok=True)
        os.makedirs(path_dl2, exist_ok=True)
        # List children for path_dl0
        children = os.listdir(path_dl0)
        for child in children:
            # Combine new path
            new__path_dl0 = os.path.join(path_dl0, child)
            new__path_dl1 = os.path.join(path_dl1, child)
            new__path_dl2 = os.path.join(path_dl2, child)
            # Publish each new child
            time.sleep(time_sleep_inframessage)
            publish(new__path_dl0, new__path_dl1, new__path_dl2, F_sleep, socket, time_sleep_inframessage)
            # Change sleep status
            F_sleep = F_sleep and False



if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python dl0_publisher.py <path/to/dl0_data/> <path/to/dl1_data/> <path/to/dl2_data/> "
              "<socket> <time_sleep>")
        sys.exit(1)
    # TODO: creare due supervisor (dl02, dl01) deve derivare da Supervisor1
    # Get the DL0, DL1 and DL2 data path
    path_dl0, path_dl1, path_dl2 = sys.argv[1], sys.argv[2], sys.argv[3] 
    # Get the socket name where publishing the file name to process from DL0 to DL2
    socketstring = sys.argv[4]
    for i in range(3):
        print(f"{3-i}")
        time.sleep(1)
    time_sleep_inframessage = int(sys.argv[5])
    # Bind socket
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(socketstring)
    # Publish DL0 files recursive mode
    publish(path_dl0, path_dl1, path_dl2, True, socket, time_sleep_inframessage)