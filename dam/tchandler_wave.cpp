//
//  tchandler_wave.cpp
//  DAM_xc
//
//  Created by Alessio Aboudan on 08/10/21.
//

#include <cstdio>
#include <cstdlib>
#include <string.h>

#include "config.h"
#include "trace.h"

#include "globals.h"

#include "tchandler.h"

static inline void sendHeader(uint32_t *waveBuff) {
    
    if (g_ctrlServer.getState() == TcpServer::STT_ACTIVE) {
    
        static const size_t buffSz = sizeof(Header)+sizeof(Data_WaveHeader);
        uint8_t buff[buffSz];
        
        memset(buff, 0, buffSz);

        Header* header = (Header*)buff;
        header->apid     = Header::CLASS_TM + (uint16_t)g_configInfo.damApid;
        header->sequence = Header::GROUP_FIRST + (uint16_t)g_systemInfo.getPacketCount();
        header->type     = Data_WaveHeader::TYPE;
        header->subType  = Data_WaveHeader::SUB_TYPE;
        header->size     = sizeof(Data_WaveHeader);

        uint32_t *data = (uint32_t*)(buff+sizeof(Header));
        
        *data = g_configInfo.damRunID;
        data++;
        
        *data = g_configInfo.damSessionID;
        data++;
        
        *data = g_configInfo.damConfigID;
        data++;
        
        memcpy(data, waveBuff, 24);
        
        //data->encode();
        header->encode();
    
        // TODO: handle return errors
        g_ctrlServer.send(buff, buffSz);
        
        //TRACE("sendHeader %d bytes\n", buffSz);
        
    }
    
}

static inline void sendData(uint32_t *waveBuff, uint32_t waveBuffSz, bool last) {
    
    if (g_ctrlServer.getState() == TcpServer::STT_ACTIVE) {
    
        static const size_t buffSz = sizeof(Header)+sizeof(Data_WaveData);
        uint8_t buff[buffSz];

        memset(buff, 0, buffSz);

        Header* header = (Header*)buff;
        header->apid     = Header::CLASS_TM + (uint16_t)g_configInfo.damApid;
        if (last) {
            header->sequence = Header::GROUP_LAST + (uint16_t)g_systemInfo.getPacketCount();
        } else {
            header->sequence = Header::GROUP_CONT + (uint16_t)g_systemInfo.getPacketCount();
        }
        header->type     = Data_WaveData::TYPE;
        header->subType  = Data_WaveData::SUB_TYPE;
        header->size     = waveBuffSz*4;

        uint32_t *data = (uint32_t*)(buff+sizeof(Header));
        
        memcpy(data, waveBuff, waveBuffSz*4);
        
        //data->encode();
        header->encode();
        
        // TODO: handle return errors
        g_ctrlServer.send(buff, sizeof(Header) + waveBuffSz*4);
        
        //TRACE("sendData %d bytes\n", sizeof(Header) + waveBuffSz*4);
        
    }
}

int TcHandler::sendWaveform(uint32_t *waveBuff, uint32_t waveBuffSz) {
    
    // TODO: check that the buffer size if big enough to contain data
    
    int res = sendBegin();
    if (res == 0) {
            
        sendHeader(waveBuff);
        waveBuff += 6;
        waveBuffSz -= 6;
        
        for (int i = 0; i < 24; i++) {
            
            if (waveBuffSz > U32_X_PACKET) {
                
                sendData(waveBuff, U32_X_PACKET, false);
                waveBuff += U32_X_PACKET;
                waveBuffSz -= U32_X_PACKET;
                
            } else {
                
                sendData(waveBuff, waveBuffSz, true);
                break;
                
            }
            
        }
        
        sendEnd();
            
        return 0;
            
    } else {
        return -1;
    }
    
    
    return 0;
    
}
