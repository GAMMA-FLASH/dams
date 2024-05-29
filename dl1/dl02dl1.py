# import argparse
from snapeventlist import EventlistSnapshot

def main():
    # parser = argparse.ArgumentParser(description='This routine converts an h5 file from type dl0 to dl1,'
    #                                              'selecting from a waveform with more than 16k samples'
    #                                              'to a smaller waveform in which the peak and the background'
    #                                              'around it are reported.')    
    # Add the args
    # parser.add_argument('source', type=str, help='Source file h5')
    # parser.add_argument('dest', type=str, help='Dest file h5')
    # parser.add_argument('startEvent', type=str, help='Index of start wf, 0 otherwise')
    # parser.add_argument('endEvent', type=str, help='Index of final wf, -1 otherwise')
    # Parse arguments
    # args = parser.parse_args()
    # Extract the parameters
    # source      = args.source
    # /home/usergamma/workspace/dams/dl1
    source      = '/home/usergamma/workspace/dams/dl1/prova.h5'
    # dest        = args.dest
    dest        = '/home/usergamma/workspace/Data/DL1'
    xml_path    = '/home/usergamma/workspace/dams/dl1/DL1model.xml'
    config_path = '/home/usergamma/workspace/dams/dl1/dl02dl1_config.json'
    # startEvent  = int(args.startEvent)
    startEvent  = 0
    # endEvent    = int(args.endEvent)
    endEvent    = -1
    snap_evlist = EventlistSnapshot(config_path, xml_path)
    snap_evlist.process_file(source, dest, startEvent=startEvent, endEvent=endEvent)

if __name__ == "__main__":
    main()