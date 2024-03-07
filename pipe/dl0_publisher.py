import zmq
import json
import time
import sys
import os

from printcolors import colore_verde, reset_colore

class DL0_Publisher:
    def __init__(self, path_dl0, path_dl1, path_dl2) -> None:
        self.path_dl0 = path_dl0
        if not os.path.exists(self.path_dl0):
            raise Exception(f"Source path {path_dl0} does not exist!")
        self.path_dl1 = path_dl1
        if not os.path.exists(self.path_dl1):
            raise Exception(f"Source path {path_dl1} does not exist!")
        self.path_dl2 = path_dl2
        if not os.path.exists(self.path_dl2):
            raise Exception(f"Source path {path_dl0} does not exist!")
        self.list_fileH5 = os.listdir(self.path_dl0)
        self.list_fileH5 = list(filter(lambda f: '.h5' in f, self.list_fileH5))

    def publish_filenames(self, socketstring):
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.bind(socketstring)
        F_sleep = True
        for filename in self.list_fileH5:
            if F_sleep:
                time.sleep(1)
                F_sleep = False
            data = {"path_dl0_folder": self.path_dl0, 
                    "path_dl1_folder": self.path_dl1, 
                    "path_dl2_folder": self.path_dl2, 
                    "filename":        filename}
            message = json.dumps(data)
            socket.send_string(message)
            print(f"Sent: {colore_verde}{message}{reset_colore}")
            # time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python dl0_publisher.py <path/to/dl0_data/> <path/to/dl1_data/> <path/to/dl2_data/> "
              "<socket>")
        sys.exit(1)
    # TODO: creare due supervisor (dl02, dl01) deve derivare da Supervisor1
    # Get the DL0, DL1 and DL2 data path
    path_dl0, path_dl1, path_dl2 = sys.argv[1], sys.argv[2], sys.argv[3] 
    # Get the socket name where publishing the file name to process from DL0 to DL2
    socketstring = sys.argv[4]
    for i in range(3):
        print(f"{3-i}")
        time.sleep(1)
    pub_dl0 = DL0_Publisher(path_dl0, path_dl1, path_dl2)
    pub_dl0.publish_filenames(socketstring)