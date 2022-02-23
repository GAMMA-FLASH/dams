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
        header->runID	 = (uint16_t)g_configInfo.damRunID;
        header->size     = sizeof(Data_WaveHeader);
        
        Data_WaveHeader* data = (Data_WaveHeader*)(buff+sizeof(Header));
        
        data->type     = Data_WaveHeader::TYPE;
        data->subType  = Data_WaveHeader::SUB_TYPE;
        
        data->sessionID = (uint16_t)g_configInfo.damSessionID;
        data->configID = (uint16_t)g_configInfo.damConfigID;
        
        // Get time status
        data->timeSts = *(uint8_t*)(waveBuff+8);
        
        if (data->timeSts == 0) { // Time is valid
        	
        	TimeStamp::AbsoluteTime absTime;
			g_timeStamp.computeAbsoluteTime((struct timespec*)(waveBuff+6), (TimeStamp::CurrentTime*)waveBuff, &absTime);
        	
        	if (absTime.ppsSliceNo > 0xFF) {
        		data->ppsSliceNo = 0xFF;
        		data->timeSts += TimeStamp::TS_OVFLOW;
        	} else {
        		data->ppsSliceNo = (uint8_t)absTime.ppsSliceNo;
        	}
        	
        	data->year = absTime.year;
        	data->month = absTime.month;
        	
        	data->_p32[3] = absTime._p32[1];
        	data->_p32[4] = absTime._p32[2];
        	
        } 
        
		//printf("W %02X %04d %02d %02d %02d %02d %02d %02d %06d\n", data->timeSts, data->ppsSliceNo, data->year, data->month, data->day, data->hh, data->mm, data->ss, data->us); 
        
        memcpy(&data->ts, waveBuff+6, 24);
        
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
        header->runID	 = (uint16_t)g_configInfo.damRunID;
        header->size     = 4 + waveBuffSz*4;

        Data_WaveData *data = (Data_WaveData*)(buff+sizeof(Header));
        data->type     = Data_WaveData::TYPE;
        data->subType  = Data_WaveData::SUB_TYPE;
        
        memcpy(data->buff, waveBuff, waveBuffSz*4);
        
        //data->encode();
        header->encode();
        
        // TODO: handle return errors
        g_ctrlServer.send(buff, sizeof(Header) + 4 + waveBuffSz*4);
        
        //TRACE("sendData %d bytes\n", sizeof(Header) + waveBuffSz*4);
        
    }
}

int TcHandler::sendWaveform(uint32_t *waveBuff, uint32_t waveBuffSz) {
    
    // TODO: check that the buffer size if big enough to contain data
    
    int res = sendBegin();
    if (res == 0) {
            
        // Waveform header from FPGA
        sendHeader(waveBuff);
        waveBuff += 12;
        waveBuffSz -= 12;
        
        for (int i = 0; i < 24; i++) {
        
            if (waveBuffSz > U32_X_PACKET) {
            
            	//TRACE("Part [%02d] rem %08d size %8d\n", i, waveBuffSz, U32_X_PACKET);
                
                sendData(waveBuff, U32_X_PACKET, false);
                waveBuff += U32_X_PACKET;
                waveBuffSz -= U32_X_PACKET;
                
            } else {
            
            	//TRACE("Part [%02d] rem %8d size %08d\n", i, waveBuffSz, waveBuffSz);
                
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
