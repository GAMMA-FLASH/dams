import os
import argparse
import subprocess
import sys
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
        f"{args.path_dl0}" + f"{'/'+args.acquisition if not args.acquisition is None else ''}", 
        f"{args.path_dl1}" + f"{'/'+args.acquisition if not args.acquisition is None else ''}", 
        f"{args.path_dl2}" + f"{'/'+args.acquisition if not args.acquisition is None else ''}", 
        args.socket_dl0pub, "1"
    ])

########################################################################################################################

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
        f"Supervisor_DL0toDL2('{args.config_json_path}', 'DL0toDL2')"
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
        f"Supervisor_DL0toDL1('{args.config_json_path}', 'DL0toDL1')"
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
        f"Supervisor_DL1toDL2('{args.config_json_path}', 'DL1toDL2')"
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
        f"Supervisor_DL2CCK('{args.config_json_path}', 'DL2Checker').start()"
    )
    subprocess.run(["python", "-c", exec_command])

########################################################################################################################

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
        f"{args.config_json_path}"
    ])

########################################################################################################################

def send_command(args):
    """
    Stop all service.
    
    Parameters:
        args (Namespace): Parsed command-line arguments containing paths and socket configurations.
    """
    print("========= SENDING Command ========")
    if not args.command_type or not args.target_processname:
        print("Error: --command-type and --target-processname are required for this action.")
        sys.exit(1)
    subprocess.run([
        "python", "/home/gamma/dependencies/rta-dataprocessor/workers/SendCommand.py",
        f"{args.config_json_path}", f"{args.command_type}", f"{args.target_processname}"
    ])

def send_config(args):
    """
    Stop all service.
    
    Parameters:
        args (Namespace): Parsed command-line arguments containing paths and socket configurations.
    """
    print("========= SENDING Configuration ========")
    if not args.detector_config or not args.target_processname:
        print("Error: --detector-config and --target-processname are required for this action.")
        sys.exit(1)
    subprocess.Popen([
        "python", "/home/gamma/dependencies/rta-dataprocessor/workers/SendConfig.py",
        f"{args.config_json_path}", "DL0toDL2", f"{args.detector_config}"
    ]).communicate()
    time.sleep(1)
    subprocess.Popen([
        "python", "/home/gamma/dependencies/rta-dataprocessor/workers/SendConfig.py",
        f"{args.config_json_path}", "DL0toDL1", f"{args.detector_config}"
    ]).communicate()
    time.sleep(1)
    subprocess.Popen([
        "python", "/home/gamma/dependencies/rta-dataprocessor/workers/SendConfig.py",
        f"{args.config_json_path}", "DL1toDL2", f"{args.detector_config}"
    ]).communicate()
    time.sleep(1)
    subprocess.Popen([
        "python", "/home/gamma/dependencies/rta-dataprocessor/workers/SendConfig.py",
        f"{args.config_json_path}", "DL2Checker", f"{args.path_out_json}"
    ]).communicate()

########################################################################################################################

def run_silent_test(args):
    """
    Esegue una serie di test definiti automaticamente senza output sulla console.
    """
    print("========= RUNNING SILENT TESTS ========")

    print("Eseguendo test automatici in background...")

    # Creazione della cartella dei log se non esiste
    log_dir = "/home/gamma/workspace/Out/logs/nohup"
    os.makedirs(log_dir, exist_ok=True)

    # Definizione dei comandi di test
    test_commands = [
        (["python", "test_GammaFlash.py", "-N", "1"], None),
        (["python", "test_GammaFlash.py", "-N", "2"], None),
        (["python", "test_GammaFlash.py", "-N", "3"], None),
        (["python", "test_GammaFlash.py", "-N", "4"], None),
        # Sleep di 5 secondi
        (["python", "/home/gamma/workspace/dams/setup/wait_for_rtadp.py", args.config_json_path, "15", "--extended"], "wait_pipe_start.log"),
        (["python", "test_GammaFlash.py", "-N", "30", "-o", "/home/gamma/workspace/Out/json", "-d", "/home/gamma/workspace/dams/dl1/detectorconfig_PMT.json", "-t", "all"], "send_config.log"),
        # Sleep di 5 secondo
        ("sleep 5", None),
        (["python", "test_GammaFlash.py", "-N", "20", "-c", "start", "-t", "all"], "start_command.log"),
        # Sleep di 5 secondo
        ("sleep 5", None),
        (["python", "test_GammaFlash.py", "-N", "0", "-acq", args.acquisition], "producer.log"),
    ]

    # Lancio dei comandi in background con `nohup`
    for cmd, log_file in test_commands:
        if isinstance(cmd, str) and cmd.startswith("sleep"):
            sleep_time = int(cmd.split()[1])  # Estrae il numero di secondi
            print(f"Waiting for {sleep_time} seconds...")
            time.sleep(sleep_time)
            continue  # Non eseguire sleep con subprocess
        
        # Gestione dei file di log
        log_path = os.path.join(log_dir, log_file) if log_file else "/dev/null"
        
        # Lancio del comando con subprocess.Popen
        with open(log_path, "w") as log:
            p = subprocess.Popen(cmd, stdout=log, stderr=log, shell=False)
            if log_file == "wait_pipe_start.log":
                print("wait starting services...")
                p.communicate()
                print("The whole Pipe si now up! Continue...")

    print(f"I test sono stati avviati in background. I log sono salvati in {log_dir}")
    # NOTE: PER TERMINARE TUTTI I PROCESSI USA QUESTO COMANDO:
    #      pkill -f python
    #      pkill -9 -f python
    print("========= SILENT TESTS COMPLETED ========")

########################################################################################################################

def main():
    """
    Main function to parse command-line arguments and execute the corresponding service.
    """
    parser = argparse.ArgumentParser(description="Script to start various GammaFlash services.")
    parser.add_argument(
        "-N", "--service-number", 
        type=int, choices=[0, 1, 2, 3, 4, 5, 10, 20, 30],
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
            ##########
            "30: Send detector config\n"
        )
    )
    # PATH TO DLx data 
    parser.add_argument("-dl0", "--path-dl0", 
                        default="/home/gamma/workspace/Data/DL0", 
                        help="Path to DL0 data")
    parser.add_argument("-dl1", "--path-dl1", 
                        default="/home/gamma/workspace/Data/DL1", 
                        help="Path to DL1 data")
    parser.add_argument("-dl2", "--path-dl2", 
                        default="/home/gamma/workspace/Data/DL2", 
                        help="Path to DL2 data")
    parser.add_argument("-acq", "--acquisition",
                        default=None,
                        help="Acquisition name if you want to run an experiment on a single acquisition")
    # SOCKET 
    parser.add_argument("-spub", "--socket-dl0pub", 
                        default="tcp://localhost:5515", 
                        help="Socket for DL0Publisher")
    parser.add_argument("-scck", "--socket-cck", 
                        default="tcp://localhost:5559", 
                        help="Socket for DL2Publisher")
    # JSON FILE PATH
    parser.add_argument("-i", "--config-json-path", 
                        default="/home/gamma/workspace/dams/pipe/config.json", 
                        help="Path to JSON configuration")
    parser.add_argument("-o", "--path-out-json", 
                        default="/home/gamma/workspace/Out/json", 
                        help="Path to JSON results")
    parser.add_argument("-d", "--detector-config", 
                        default="/home/gamma/workspace/dams/dl1/detectorconfig_PMT.json",
                        help="Detectort configuration file path.")
    # COMMAND 
    parser.add_argument("-c", "--command-type", 
                        default="start",
                        help="Command type for sending command")
    parser.add_argument("-t", "--target-processname", 
                        default="all",
                        help="Target process name for sending command")
    # SILENT CALL
    parser.add_argument("--silenttest", action="store_true", help="Esegue i test in modalità silenziosa")

    args = parser.parse_args()

    if args.silenttest:
        run_silent_test(args)
        return  # Evita di eseguire altro codice se il test è in corso

    actions = {
        0: start_dl0_publisher,
        1: start_dl0todl2_service,
        2: start_dl0todl1_service,
        3: start_dl1todl2_service,
        4: start_dl2_checker,
        5: start_dl2_publisher,
        10: monitoring,
        20: send_command,
        30: send_config,
    }

    action = actions.get(args.service_number)
    if action:
        action(args)
    else:
        print("Unknown argument!")

if __name__ == "__main__":
    main()