import os
from eventlist_v4 import Eventlist
import argparse

def main1():
    parser = argparse.ArgumentParser(description='This routine converts an h5 file from type DL0 to DL2.')    
    # Add the args
    parser.add_argument('source', type=str, help='Source file h5')
    parser.add_argument('dest', type=str, help='Dest folder')
    parser.add_argument('startEvent', type=str, help='Index of start wf, 0 otherwise')
    parser.add_argument('endEvent', type=str, help='Index of final wf, -1 otherwise')
    # Parse arguments
    args = parser.parse_args()
    # Extract the parameters
    source      = args.source
    dest        = args.dest
    startEvent  = int(args.startEvent)
    endEvent    = int(args.endEvent)
    # source      = '/home/usergamma/workspace/dams/dl1/prova.h5'
    # dest        = '/home/usergamma/workspace/Data/DL0toDL2'
    # startEvent  = 0
    # endEvent    = -1
    eventlist = Eventlist()
    eventlist.process_file(source, None, dest, startEvent=startEvent, endEvent=endEvent)

if __name__ == "__main__":
    main1()
