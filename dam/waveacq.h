//
//  waveacq.h
//  DAM_xc
//
//  Created by Alessio Aboudan on 04/10/21.
//

#ifndef __WAVEACQ_H__
#define __WAVEACQ_H__

#include <pthread.h>

class WaveAcq {
    
public:
    
    WaveAcq();
    ~WaveAcq();
    
    int init();
    int destroy();
    
protected:
    
private:
    
    bool threadStarted;
    pthread_t acqThreadInfo;
    pthread_t sendThreadInfo;
    
};

#endif // __WAVEACQ_H__
