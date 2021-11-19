//
//  fifo.h
//  Fifo2
//
//  Created by Alessio Aboudan on 22/10/21.
//

#ifndef __FIFO_H__
#define __FIFO_H__

#include <cstdio>
#include <cstdint>

#include <pthread.h>
#include <semaphore.h>

class Fifo {
  
public:
    
    Fifo(uint32_t maxBuffNo, uint32_t maxBuffSz, uint32_t* buff);
    ~Fifo();
    
    void init();
    
    void pushGet(uint32_t **buff);
    void pushRelease();
    
    void popGet(uint32_t **buff);
    void popRelease();
    
protected:
    
    uint32_t buffNo;
    uint32_t buffSz;
    uint32_t *buff;
    uint32_t pushOff;
    uint32_t popOff;
    
    sem_t empty;
    sem_t full;
    
};

#endif // __FIFO_H__
