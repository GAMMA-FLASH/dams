//
//  tcp.h
//  DAM_xc
//
//  Created by Alessio Aboudan on 24/02/21.
//

#ifndef __TCP_H__
#define __TCP_H__

#include <netinet/in.h>

class TcpServer {
  
public:
    
    enum Result {
        RES_OK = 0,
        RES_NOK = -1
    };
    
    enum State {
        STT_CLOSED    = 0x00,
        STT_OPEN,
        STT_ACCEPT,
        STT_ACTIVE
    };
    
    TcpServer();
    ~TcpServer();
    
    int open(int portNo);
    void close();
    
    // To be called by a single thread
    int recv(void *buffer, size_t bufferSz);
    
    // This shall be thread safe because it could be called both by TC execution thread and by the
    // data acquisition thread.
    // Socket send is a syscall, it is an atomic operation with no race conditions in the kernel.
    // So even though send() is thread-safe, synchronisation is required to ensure that the bytes
    // from different send calls are merged into the byte stream in a predictable manner. Note that
    // if the size of send buffer is le to the size of the kernel buffer then synchronisation
    // my not be needed (TBC)
    int send(const void *buffer, size_t bufferSz);
    
    int getState() {return state;};
    
protected:
    
    int state;
    int listenFd;
    struct sockaddr_in saddr;
    int connFd;
    struct sockaddr_in caddr;
    socklen_t caddrSz;
    
};

#endif // __TCP_H__
