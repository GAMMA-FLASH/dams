//
//  systeminfo.h
//  DAM_xc
//
//  Created by Alessio Aboudan on 26/02/21.
//

#ifndef __SYSTEMINFO_H__
#define __SYSTEMINFO_H__

#include <stdio.h>

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
        FLG_PPS_NOK         = 0x80,
        FLG_GPS_NOK         = 0x40,
        FLG_TRG_ERR			= 0x20
    };
    
    uint32_t state;
    uint32_t flags;
    
    uint32_t totAcqWaveCount;
    uint32_t totSentWaveCount;
    
    uint32_t waveCount;
    
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
