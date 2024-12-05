import subprocess
# Supervisors
from DL0toDL2__service.Supervisor_gflash import Supervisor_DL0toDL2
from DL0toDL1__service.Supervisor_gflash import Supervisor_DL0toDL1
from DL1toDL2__service.Supervisor_gflash import Supervisor_DL1toDL2


def main():
    path_dl0='/home/gamma/workspace/Data/DL0' 
    path_dl1='/home/gamma/workspace/Data/DL1' 
    path_dl2='/home/gamma/workspace/Data/DL2' 
    socket='tcp://127.0.0.1:5551'
    json_path_Dl0toDL2='/home/gamma/workspace/dams/DL0toDL2__service/config.json'
    json_path_Dl0toDL1='/home/gamma/workspace/dams/DL0toDL1__service/config.json'
    json_path_Dl1toDL2='/home/gamma/workspace/dams/DL1toDL2__service/config.json'
    print(0)
    # Start supervisor for DL0toDL2
    supervisor_DL0toDL2 = Supervisor_DL0toDL2(json_path_Dl0toDL2, 'DL0toDL2')
    supervisor_DL0toDL2.start()
    print(1)
    # Start supervisor for DL0toDL1
    supervisor_DL0toDL1 = Supervisor_DL0toDL1(json_path_Dl0toDL1, 'DL0toDL1')
    supervisor_DL0toDL1.start()
    print(2)
    # Start supervisor for DL1toDL2
    supervisor_DL1toDL2 = Supervisor_DL1toDL2(json_path_Dl1toDL2, 'DL1toDL2')
    supervisor_DL1toDL2.start()
    print(3)
    # Create command publisher
    command_pub = f'python dl0_publisher.py {path_dl0} {path_dl1} {path_dl2} {socket}'
    subprocess.run(command_pub)
    print(4)

if __name__ == "__main__":
    main()