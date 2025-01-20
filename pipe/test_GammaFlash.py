import os
import argparse
import subprocess
import time

def start_dl0_publisher(args):
    """
    Start the DL0Publisher service.
    
    Parameters:
        args (Namespace): Parsed command-line arguments containing paths and socket configurations.
    """
    print("========= START DL0Publisher ========")
    subprocess.run([
        "python", "publisher_dl0.py",
        args.path_dl0, args.path_dl1, args.path_dl2, args.socket_dl0pub, "1"
    ])

def start_dl0todl2_service(args):
    """
    Start the DL0toDL2 service and clear the DL2 directory.
    
    Parameters:
        args (Namespace): Parsed command-line arguments containing paths and socket configurations.
    """
    print("========= START DL0toDL2__service ========")
    # for file in os.listdir(args.path_dl2):
    #     os.remove(os.path.join(args.path_dl2, file))
    exec_command = (
        "from DL0toDL2__service.Supervisor_dl0todl2 import Supervisor_DL0toDL2; "
        f"Supervisor_DL0toDL2('{args.json_path}', 'DL0toDL2')"
    )
    p = subprocess.run(["python", "-c", exec_command])
    print(p.stdout)
    print(p.stderr)

def start_dl0todl1_service(args):
    """
    Start the DL0toDL1 service and clear the DL1 directory.
    
    Parameters:
    """
    print("========= START DL0toDL1__service ========")
    # for file in os.listdir(args.path_dl1):
    #    os.remove(os.path.join(args.path_dl1, file))
    exec_command = (
        "from DL0toDL1__service.Supervisor_dl0todl1 import Supervisor_DL0toDL1; "
        f"Supervisor_DL0toDL1('{args.json_path}', 'DL0toDL1')"
    )
    subprocess.run(["python", "-c", exec_command])

def start_dl1todl2_service(args):
    """
    Start the DL1toDL2 service and clear the DL2 directory.
    
    Parameters:
        args (Namespace): Parsed command-line arguments containing paths and socket configurations.
    """
    print("========= START DL1toDL2__service ========")
    # for file in os.listdir(args.path_dl2):
    #    os.remove(os.path.join(args.path_dl2, file))
    exec_command = (
        "from DL1toDL2__service.Supervisor_dl1todl2 import Supervisor_DL1toDL2; "
        f"Supervisor_DL1toDL2('{args.json_path}', 'DL1toDL2')"
    )
    subprocess.run(["python", "-c", exec_command])

def start_dl2_checker(args):
    """
    Start the DL2Checker service and clear the JSON results directory.
    
    Parameters:
        args (Namespace): Parsed command-line arguments containing paths and socket configurations.
    """
    print("========= START DL2Checker ========")
    # for file in os.listdir(args.path_json_result):
    #     os.remove(os.path.join(args.path_json_result, file))
    exec_command = (
        "from DL2Checker__service.Supervisor_checker import Supervisor_DL2CCK; "
        f"Supervisor_DL2CCK('{args.json_path}', 'DL2Checker').start()"
    )
    subprocess.run(["python", "-c", exec_command])

def start_dl2_publisher(args):
    """
    Start the DL2Publisher service.
    
    Parameters:
        args (Namespace): Parsed command-line arguments containing paths and socket configurations.
    """
    print("========= START DL2Publisher ========")
    subprocess.run([
        "python", "publisher_CCK.py",
        args.path_dl2, args.socket_cck
    ])

########################################################################################################################

def monitoring(args):
    """
    Start the Process Monitoring.
    
    Parameters:
        args (Namespace): Parsed command-line arguments containing paths and socket configurations.
    """
    print("========= START Monitoring ========")
    subprocess.run([
        "python", "/home/gamma/dependencies/rta-dataprocessor/workers/ProcessMonitoring.py",
        f"{args.json_path}"
    ])

########################################################################################################################

def send_command(args):
    """
    Stop all service.
    
    Parameters:
        args (Namespace): Parsed command-line arguments containing paths and socket configurations.
    """
    print("========= START Monitoring ========")
    if not args.command_type or not args.target_processname:
        print("Error: --command-type and --target-processname are required for this action.")
        sys.exit(1)
    subprocess.run([
        "python", "/home/gamma/dependencies/rta-dataprocessor/workers/SendCommand.py",
        f"{args.json_path}", f"{args.command_type}", f"{args.target_processname}"
    ])

########################################################################################################################

def main():
    """
    Main function to parse command-line arguments and execute the corresponding service.
    """
    parser = argparse.ArgumentParser(description="Script to start various GammaFlash services.")
    parser.add_argument(
        "-N", "--service-number", 
        type=int, choices=[0, 1, 2, 3, 4, 5, 10, 20],
        help=(
            "0: Start DL0Publisher\n"
            "1: Start DL0toDL2__service\n"
            "2: Start DL0toDL1__service\n"
            "3: Start DL1toDL2__service\n"
            "4: Start DL2Checker__service\n"
            "5: Start Publisher_CCK\n"
            ##########
            "10: Start Monitoring\n"
            ##########
            "20: Send command\n"
        )
    )
    parser.add_argument("-dl0", "--path-dl0", 
                        default="/home/gamma/workspace/Data/DL0", 
                        help="Path to DL0 data")
    parser.add_argument("-dl1", "--path-dl1", 
                        default="/home/gamma/workspace/Data/DL1", 
                        help="Path to DL1 data")
    parser.add_argument("-dl2", "--path-dl2", 
                        default="/home/gamma/workspace/Data/DL2", 
                        help="Path to DL2 data")
    parser.add_argument("-jr", "--path-json-result", 
                        default="/home/gamma/workspace/Out/json", 
                        help="Path to JSON results")
    parser.add_argument("-spub", "--socket-dl0pub", 
                        default="tcp://localhost:5555", 
                        help="Socket for DL0Publisher")
    parser.add_argument("-scck", "--socket-cck", 
                        default="tcp://localhost:5559", 
                        help="Socket for DL2Publisher")
    parser.add_argument("-f", "--json-path", 
                        default="/home/gamma/workspace/dams/pipe/config.json", 
                        help="Path to JSON configuration")
    parser.add_argument("-c", "--command-type", 
                        default="start",
                        help="Command type for sending command")
    parser.add_argument("-t", "--target-processname", 
                        default="all",
                        help="Target process name for sending command")

    args = parser.parse_args()

    actions = {
        0: start_dl0_publisher,
        1: start_dl0todl2_service,
        2: start_dl0todl1_service,
        3: start_dl1todl2_service,
        4: start_dl2_checker,
        5: start_dl2_publisher,
        10: monitoring,
        20: send_command,
    }

    action = actions.get(args.service_number)
    if action:
        action(args)
    else:
        print("Unknown argument!")

if __name__ == "__main__":
    main()