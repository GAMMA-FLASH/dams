//
//  tchandler.cpp
//  DAM_xc
//
//  Created by Alessio Aboudan on 26/08/21.
//

#include <cstdio>
#include <cstdlib>
#include <string.h>

#include "config.h"
#include "trace.h"

#include "globals.h"

#include "tchandler.h"

// Stub function
void *recvTcThreadFcn(void *ptr) {
    
    // Cast to class pointer
    TcHandler *p = (TcHandler*)ptr;
    
    // Enter TC rx loop
    p->recvTc();
    
    // This point should never be reached
    return EXIT_SUCCESS;
    
}

TcHandler::TcHandler() {
    threadStarted = false;
}

TcHandler::~TcHandler() {
    if (threadStarted) {
        pthread_cancel(recvTcThreadInfo);
        pthread_join(recvTcThreadInfo, NULL);
    }
}

int TcHandler::init() {
    
    pthread_mutex_init(&sendTmMutex, NULL);
    
    // Set scheduler and priority
    //pthread_attr_t tcRecvThreadAttr;
    //pthread_attr_init(&tcRecvThreadAttr);
    //pthread_attr_setinheritsched(&tcRecvThreadAttr, PTHREAD_EXPLICIT_SCHED);
    //pthread_attr_setschedpolicy(&tcRecvThreadAttr, SCHED_FIFO);
    //thread_param.sched_priority = sched_get_priority_max(SCHED_FIFO);
    //pthread_attr_setschedparam(&tcRecvThreadAttr, &thread_param);
    
    int res = pthread_create(&recvTcThreadInfo, NULL, recvTcThreadFcn, this);
    if (res >= 0) {
        threadStarted = true;
    }
    
    return res;
    
}

void TcHandler::recvTc() {
    
    // INFINITE LOOP
    for(;;) {
        
        static const size_t buffSz = 128;
        uint8_t buff[buffSz];
        
        int nbytes = g_ctrlServer.recv(buff, buffSz);
        if (nbytes > 0) {
            
            printf("[%04d] ", nbytes);
            for (int i = 0; i < nbytes; i++)
                printf("%02X", buff[i]);
            printf("\n");
            
            Header* header = (Header*)buff;
            int res = header->decode();
            if (res == 0) {
                
                header->print();
                
                res = sendBegin();
                if (res == 0) {
                
                    switch (header->type) {
                    
                        // Test
                        case 0x11:
                            switch (header->subType) {
                                case 0x01:
                                    execConnTst(header);
                                    break;
                                default:
                                    sendTcRx(header, 0xFE);
                                    break;
                            }
                            break;
                            
                        // Configuration and control
                        case 0xA0:
                            switch (header->subType) {
                                case 0x04:
                                    execStartAcq(header);
                                    break;
                                case 0x05:
                                    execStopAcq(header);
                                    break;
                                default:
                                    sendTcRx(header, 0xFE);
                                    break;
                            }
                            break;
                            
                        // TC type not implemented
                        default:
                            sendTcRx(header, 0xFF);
                            break;
                        
                    }
                    
                    sendEnd();
                
                }
            
            }
        
        }
        
    }
    
    // This point should never be reached
    
}

int TcHandler::sendBegin() {
    int res = pthread_mutex_lock(&sendTmMutex);
    return res;
}

int TcHandler::sendEnd() {
    int res = pthread_mutex_unlock(&sendTmMutex);
    return res;
}

int TcHandler::sendTcRx(Header *tcHeader, uint8_t err) {
    
    if (g_ctrlServer.getState() == TcpServer::STT_ACTIVE) {
    
        static const size_t buffSz = sizeof(Header) + sizeof(Data_TcRx);
        uint8_t buff[buffSz];

        memset(buff, 0, buffSz);

        Header* header = (Header*)buff;
        header->apid     = Header::CLASS_TM + (uint16_t)g_configInfo.damApid;
        header->sequence = Header::GROUP_STAND_ALONE + (uint16_t)g_systemInfo.getPacketCount();
        header->type     = Data_TcRx::TYPE;
        header->subType  = Data_TcRx::SUB_TYPE;
        header->size     = sizeof(Data_TcRx);
    
        Data_TcRx* data = (Data_TcRx*)(buff+sizeof(Header));
        data->err = err;
        data->apid = tcHeader->apid;
        data->sequence = tcHeader->sequence;
    
        //data->encode();
        header->encode();
    
        // TODO: handle return errors
        g_ctrlServer.send(buff, buffSz);
    
    }
    
    return 0;
    
}

int TcHandler::sendTcExec(Header *tcHeader, uint8_t err) {
    
    if (g_ctrlServer.getState() == TcpServer::STT_ACTIVE) {
    
        static const size_t buffSz = sizeof(Header) + sizeof(Data_TcExec);
        uint8_t buff[buffSz];

        memset(buff, 0, buffSz);

        Header* header = (Header*)buff;
        header->apid     = Header::CLASS_TM + (uint16_t)g_configInfo.damApid;
        header->sequence = Header::GROUP_STAND_ALONE + (uint16_t)g_systemInfo.getPacketCount();
        header->type     = Data_TcExec::TYPE;
        header->subType  = Data_TcExec::SUB_TYPE;
        header->size     = sizeof(Data_TcExec);
    
        Data_TcRx* data = (Data_TcRx*)(buff+sizeof(Header));
        data->err = err;
        data->apid = tcHeader->apid;
        data->sequence = tcHeader->sequence;
    
        //data->encode();
        header->encode();
    
        // TODO: handle return errors
        g_ctrlServer.send(buff, buffSz);
        
    }
    
    return 0;
    
}

