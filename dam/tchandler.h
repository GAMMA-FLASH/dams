//
//  tchandler.hpp
//  DAM_xc
//
//  Created by Alessio Aboudan on 26/08/21.
//

#ifndef __TCHANDLER_H__
#define __TCHANDLER_H__

#include <pthread.h>
#include <sched.h>

#include "packet.h"

class TcHandler {
    
public:
    
    TcHandler();
    ~TcHandler();

    int init();
    
    int sendHk();
    
    //int sendEvt(int type, int subType);
    
    int sendWaveform(uint32_t *buff, uint32_t buffSz);
    
    void recvTc();
    
protected:
    
    int sendBegin();
    int sendEnd();
    
    int sendTcRx(Header *tcHeader, uint8_t err);
    int sendTcExec(Header *tcHeader, uint8_t err);
    
    int execConnTst(Header *tcHeader);
    
    int execStartAcq(Header *tcHeader);
    int execStopAcq(Header *tcHeader);

private:
    
    bool threadStarted;
    pthread_t recvTcThreadInfo;
    
    pthread_mutex_t sendTmMutex;
    
};



#endif // __TCHANDLER_H__
