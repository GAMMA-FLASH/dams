import argparse
from dl02dl1_config import *
from snapeventlist import EventlistSnapshot

def main():
    parser = argparse.ArgumentParser(description='This routine converts an h5 file from type dl0 to dl1,'
                                                 'selecting from a waveform with more than 16k samples'
                                                 'to a smaller waveform in which the peak and the background'
                                                 'around it are reported.')    
    # Add the args
    parser.add_argument('source', type=str, help='Source file h5')
    parser.add_argument('dest', type=str, help='Dest file h5')
    parser.add_argument('startEvent', type=str, help='Index of start wf, 0 otherwise')
    parser.add_argument('endEvent', type=str, help='Index of final wf, -1 otherwise')
    # Parse arguments
    args = parser.parse_args()
    # Extract the parameters
    source      = args.source
    dest        = args.dest
    startEvent  = int(args.startEvent)
    endEvent    = int(args.endEvent)
    snap_evlist = EventlistSnapshot()
    snap_evlist.process_file(source, dest, startEvent=startEvent, endEvent=endEvent)

if __name__ == "__main__":
    main()