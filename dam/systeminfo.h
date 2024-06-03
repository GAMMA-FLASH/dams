//
//  systeminfo.h
//  DAM_xc
//
//  Created by Alessio Aboudan on 26/02/21.
//

#ifndef __SYSTEMINFO_H__
#define __SYSTEMINFO_H__

#include <stdio.h>
#include <atomic>

class SystemInfo {
   
public:
    
    enum State {
        STT_OFF             = 0x00, // Only for simulation/debug
        STT_STARTUP,
        STT_SERVICE,
        STT_ACQUISITION,
        STT_FAIL
    };
    
    enum Flags {
        FLG_PPS_NOK         = 0x80, // pps not received
        FLG_GPS_NOUART      = 0x40, // no signal from serial
        FLG_GPS_OVERTIME      = 0x20, // time between PPS and GGA is more than 1 second
        FLG_GPS_NOTIME      = 0x10, // invalid time wrt red pitaya time 
        FLG_TRG_ERR			= 0x01
    };
    
    uint32_t state;
    uint32_t flags;
    
    // Total acquired wforms since start
    std::atomic<unsigned int>  totAcqWformCount;
    
    // Counter used to sto acquisition
    uint32_t acqWformCount;
    
    // Wforms sent on socket
   	uint32_t sentWformCount;
     
    // Wforms saved on the current file
    uint32_t savedWformCount;
    
    // Number of files
    uint32_t fileCount;
    
    uint8_t source;
    uint32_t maxWaveNo;
    uint32_t waitUsecs;
    
    SystemInfo();
    
    int init();
     
    int getPacketCount();
    
    
protected:
    
    int packetCount;
    
    
private:
    
};

#endif // __SYSTEMINFO_H__
