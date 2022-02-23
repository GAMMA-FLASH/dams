//
//  tchandler_hk.cpp
//  DAM_xc
//
//  Created by Alessio Aboudan on 04/10/21.
//

#include <cstdio>
#include <cstdlib>
#include <string.h>

#include "config.h"
#include "trace.h"

#include "globals.h"

#include "tchandler.h"

int TcHandler::sendHk() {
    
    // TODO: handle timeout on txBegin
    int res = sendBegin();
    if (res == 0) {
            
        if (g_ctrlServer.getState() == TcpServer::STT_ACTIVE) {
        
            static const size_t buffSz = sizeof(Header) + sizeof(Data_Hk);
            uint8_t buff[buffSz];
    
            memset(buff, 0, buffSz);
    
            Header* header = (Header*)buff;
            header->apid     = Header::CLASS_TM + (uint16_t)g_configInfo.damApid;
            header->sequence = Header::GROUP_STAND_ALONE + (uint16_t)g_systemInfo.getPacketCount();
            header->runID	 = (uint16_t)g_configInfo.damRunID;
            header->size     = sizeof(Data_Hk);
    
            Data_Hk* data = (Data_Hk*)(buff+sizeof(Header));
            data->type     = Data_Hk::TYPE;
        	data->subType  = Data_Hk::SUB_TYPE;
            data->state = g_systemInfo.state;
            data->flags = g_systemInfo.flags;
            data->waveCount = g_systemInfo.waveCount;
    
            //data->encode();
            header->encode();
        
            // TODO: handle return errors
            res = g_ctrlServer.send(buff, buffSz);
            
        }
        
        sendEnd();
            
        return 0;
            
    } else {
        return -1;
    }
        
}
