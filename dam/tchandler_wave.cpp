// tchandler_wave.cpp

#include <cstdio>
#include <cstdlib>
#include <string.h>

#include "config.h"
#include "trace.h"

#include "globals.h"

#include "tchandler.h"

static inline void sendHeader(uint32_t *waveBuff) {

    // Create the packet
    static const size_t buffSz = sizeof(Header) + sizeof(Data_WaveHeader);
    uint8_t buff[buffSz];

    memset(buff, 0, buffSz);

    Header *header = (Header *)buff;
    header->apid = Header::CLASS_TM + (uint16_t)g_configInfo.damApid;
    header->sequence = Header::GROUP_FIRST + (uint16_t)g_systemInfo.getPacketCount();
    header->runID = (uint16_t)g_configInfo.damRunID;
    header->size = sizeof(Data_WaveHeader);

    Data_WaveHeader *data = (Data_WaveHeader *)(buff + sizeof(Header));

    data->type = Data_WaveHeader::TYPE;
    data->subType = Data_WaveHeader::SUB_TYPE;

    data->sessionID = (uint16_t)g_configInfo.damSessionID;
    data->configID = (uint16_t)g_configInfo.damConfigID;

    // Get time status
    data->timeSts = *(uint8_t *)(waveBuff + 8);

    if (data->timeSts == 0) { // Time is valid

        TimeStamp::AbsoluteTime absTime;
        TimeStamp::CurrentTime currTime;
        currTime.ts.tv_sec = waveBuff[6];
        currTime.ts.tv_nsec = waveBuff[7];
        currTime.hh = waveBuff[9];
        currTime.mm = waveBuff[10];
        currTime.ss = waveBuff[11];
        currTime.us = waveBuff[12];
        
        g_timeStamp.computeAbsoluteTime((struct timespec *)(waveBuff + 6), &currTime, &absTime);

        if (absTime.ppsSliceNo > 0xFF) {
            data->ppsSliceNo = 0xFF;
            data->timeSts += TimeStamp::TS_OVFLOW;
        } else {
            data->ppsSliceNo = (uint8_t)absTime.ppsSliceNo;
        }

        data->year = absTime.year;
        data->month = absTime.month;
        data->day = absTime.day;

        data->hh = absTime.hh;
        data->mm = absTime.mm;
        data->ss = absTime.ss;
        data->us = absTime.us;
    }

    memcpy(&data->ts, waveBuff + 6, 24);

    header->encode();

    // Send over socket
    if (g_ctrlServer.getState() == TcpServer::STT_ACTIVE) {

        if (g_configInfo.cfgSendWform) {

            // TODO: handle return errors
            g_ctrlServer.send(buff, buffSz);
        }
    }

    // Save on the local disk
    if (g_configInfo.cfgSaveWform) {

        // TODO: handle return errors
        g_dataStore.save(buff, buffSz);
    }
}

static inline void sendData(uint32_t *waveBuff, uint32_t waveBuffSz, bool last) {

    static const size_t buffSz = sizeof(Header) + sizeof(Data_WaveData);
    uint8_t buff[buffSz];

    memset(buff, 0, buffSz);

    Header *header = (Header *)buff;
    header->apid = Header::CLASS_TM + (uint16_t)g_configInfo.damApid;
    if (last) {
        header->sequence = Header::GROUP_LAST + (uint16_t)g_systemInfo.getPacketCount();
    } else {
        header->sequence = Header::GROUP_CONT + (uint16_t)g_systemInfo.getPacketCount();
    }
    header->runID = (uint16_t)g_configInfo.damRunID;
    header->size = 4 + waveBuffSz * 4;

    Data_WaveData *data = (Data_WaveData *)(buff + sizeof(Header));
    data->type = Data_WaveData::TYPE;
    data->subType = Data_WaveData::SUB_TYPE;

    memcpy(data->buff, waveBuff, waveBuffSz * 4);

    header->encode();

    if (g_ctrlServer.getState() == TcpServer::STT_ACTIVE) {

        if (g_configInfo.cfgSendWform) {

            // TODO: handle return errors
            g_ctrlServer.send(buff, sizeof(Header) + 4 + waveBuffSz * 4);

            if (last) {
                g_systemInfo.sentWformCount++;
            }
        }
    }

    // Save on the local disk
    if (g_configInfo.cfgSaveWform) {

        // TODO: handle return errors
        g_dataStore.save(buff, sizeof(Header) + 4 + waveBuffSz * 4);

        if (last) {
            g_systemInfo.savedWformCount++;
        }
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
