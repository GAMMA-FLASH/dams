//
//  fifo.cpp
//  Fifo2
//
//  Created by Alessio Aboudan on 22/10/21.
//

#include "fifo.h"

using namespace::std;

Fifo::Fifo(uint32_t maxBuffNo, uint32_t maxBuffSz, uint32_t* dataBuff) {
    
    buffNo = maxBuffNo;
    buffSz = maxBuffSz;
    buff = dataBuff;
    
    pushOff = 0;
    popOff = 0;
    
    sem_init(&empty, 0, buffNo);
    sem_init(&full, 0, 0);
    
}

Fifo::~Fifo() {
    sem_destroy(&empty);
    sem_destroy(&full);
}

void Fifo::init() {
    
    pushOff = 0;
    popOff = 0;
    
    sem_init(&empty, 0, buffNo);
    sem_init(&full, 0, 0);
    
} 

void Fifo::pushGet(uint32_t **outBuff) {
    
    //printf("Fifo::pushGet: %d %d\n", pushOff, popOff);
    
    // Wait for an empty buffer
    sem_wait(&empty);
    
    // Return the pointer to the buffer
    *outBuff = buff + pushOff*buffSz;
    
}

void Fifo::pushRelease() {
    
    // Update push off
    pushOff++;
    pushOff %= buffNo;
    
    // Signal the new full buffer
    sem_post(&full);
    
}

void Fifo::popGet(uint32_t **outBuff) {
    
    // Wait for a full buffer
    sem_wait(&full);
    
    // Return the pointer to the buffer
    *outBuff = buff + popOff*buffSz;
    
}

void Fifo::popRelease() {
    
    // Update pop off
    popOff++;
    popOff %= buffNo;
    
    // Signal the new empty buffer
    sem_post(&empty);
    
}
