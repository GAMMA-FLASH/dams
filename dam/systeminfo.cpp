//
//  systeminfo.cpp
//  DAM_xc
//
//  Created by Alessio Aboudan on 26/02/21.
//

#include "config.h"
#include "trace.h"

#include "systeminfo.h"

using namespace std;

SystemInfo::SystemInfo() {
    
    state = STT_SERVICE;
    flags = FLG_PPS_NOK + FLG_GPS_NOUART + FLG_GPS_OVERTIME + FLG_GPS_NOTIME + FLG_TRG_ERR;
    packetCount = 0;
    
    totAcqWformCount = 0;
    acqWformCount = 0;
   	sentWformCount = 0;
    savedWformCount = 0;
    
    fileCount = 0;
    
}

int SystemInfo::init() {
    
    return 0;
    
}

int SystemInfo::getPacketCount() {
    int res = packetCount++;
    if (packetCount >= 0x4000) { // Packet counter is 14 bit
        packetCount = 0;
    }
    return res;
}
