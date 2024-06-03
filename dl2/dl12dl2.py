import os
from eventlist_v4 import Eventlist
import argparse

def main():
    parser = argparse.ArgumentParser(description='This routine converts an h5 file from type DL1 to DL2.')    
    # Add the args
    parser.add_argument('source', type=str, help='Source file h5')
    parser.add_argument('dest', type=str, help='Dest folder')
    parser.add_argument('startEvent', type=str, help='Index of start wf, 0 otherwise')
    parser.add_argument('endEvent', type=str, help='Index of final wf, -1 otherwise')
    parser.add_argument('dl1model', type=str, help='DL1 XML model path')
    # Parse arguments
    args = parser.parse_args()
    # Extract the parameters
    source      = args.source
    dest        = args.dest
    startEvent  = int(args.startEvent)
    endEvent    = int(args.endEvent)
    xml_path    = args.dl1model
    # source      = '/home/usergamma/workspace/Data/DL1/prova.dl1.h5'
    # dest        = args.dest
    # dest        = '/home/usergamma/workspace/Data/DL1toDL2'
    # startEvent  = 0
    # endEvent    = -1
    eventlist = Eventlist(from_dl1=True, xml_model_path=xml_path)
    # eventlist.process_file(source, None, dest, startEvent=startEvent, endEvent=endEvent)
    eventlist.process_file(source, None, dest, startEvent=startEvent, endEvent=endEvent)


if __name__ == "__main__":
    main()
