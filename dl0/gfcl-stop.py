import psutil
import signal

# Find all running processes
for process in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
    try:
        # Get the process name
        process_name = process.info['name']
        # Get the command line arguments
        cmdline = process.info['cmdline']
        
        # Check if the process name is "python" and if "gfcl.py" is in the command line parameters
        if process_name == 'python' and 'gfcl.py' or process_name == 'python3.9' and 'gfcl.py' in cmdline:
            # Terminate the process
            pid = process.info['pid']
            p = psutil.Process(pid)
            p.terminate()
            print(f"Process with pid {pid} stopped.")
    
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

