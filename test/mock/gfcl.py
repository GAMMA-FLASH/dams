import argparse
import os
import signal
import time

def signal_handler(sig, frame):
    print("SIGINT received. Exiting gracefully...")
    exit(0)

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Dummy Application")
    parser.add_argument('--addr', type=str, required=True, help='IP Address to bind')
    parser.add_argument('--port', type=int, required=True, help='Port number to use')
    parser.add_argument('--outdir', type=str, required=True, help='Output directory')
    parser.add_argument('--wformno', type=int, required=True, help='Waveform number')

    args = parser.parse_args()

    # Simulate application startup
    print(f"Starting application with address {args.addr}:{args.port}")
    print(f"Output directory set to {args.outdir}")
    print(f"Waveform number is {args.wformno}")

    # Set up SIGINT handler
    signal.signal(signal.SIGINT, signal_handler)

    # Ensure the output directory exists
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    # Simulate long-running process with sleep
    try:
        while True:
            print("Application is running... Press Ctrl+C to exit.")
            time.sleep(1)
    except KeyboardInterrupt:
        # Handle Ctrl+C
        print("Keyboard interrupt received. Exiting gracefully...")
        exit(0)

if __name__ == "__main__":
    main()
