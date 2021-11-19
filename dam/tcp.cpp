//
//  tcp.cpp
//  DAM_xc
//
//  Created by Alessio Aboudan on 24/02/21.
//

#include <strings.h>
#include <unistd.h>

#include "config.h"
#include "trace.h"

#include "tcp.h"

using namespace std;

TcpServer::TcpServer() {
    
    state = STT_CLOSED;
    listenFd = -1;
    connFd = -1;
    
}

TcpServer::~TcpServer() {
    close();
}

int TcpServer::open(int portNo) {
    
    if (state == STT_CLOSED) {
        
        // Open socket
        listenFd = socket(AF_INET, SOCK_STREAM, 0);
        if (listenFd < 0) {
            TRACE("TcpServer::open: Error: socket\n");
            return RES_NOK;
        }
        
        // Trick to reuse the port immediately after stopping the server
        int optval = 1;
        setsockopt(listenFd, SOL_SOCKET, SO_REUSEADDR, (const void *)&optval , sizeof(int));
        
        // Bind socket
        bzero((char *)&saddr, sizeof(saddr));
        saddr.sin_family = AF_INET;
        saddr.sin_addr.s_addr = INADDR_ANY;
        saddr.sin_port = htons(portNo);
        if (bind(listenFd, (struct sockaddr *)&saddr, sizeof(saddr)) < 0) {
            TRACE("TcpServer::open: Error: bind\n");
            return RES_NOK;
        }
        
        // Listen (makes the socket a server socket)
        if(listen(listenFd, 1) < 0) {
            TRACE("TcpServer::open: Error: listen\n");
            return RES_NOK;
        }

        state = STT_OPEN;
        
    }
    
    return RES_OK;
    
}

void TcpServer::close() {
    
    if (state != STT_CLOSED) {
        
        ::close(connFd); // Call the posix close
        connFd = -1;
        
        ::close(listenFd);
        listenFd = -1;
        
        state = STT_CLOSED;
        
    }
    
}

int TcpServer::recv(void *buffer, size_t bufferSz) {
    
    int res;
    
    switch (state) {
        
        case STT_OPEN:

            state = STT_ACCEPT;

            // Accept a connection (creates a new connection, the old one is still active to listeninig)
            caddrSz = sizeof(caddr);
            connFd = accept(listenFd, (struct sockaddr *)&caddr, &caddrSz);
            if (connFd < 0) {
                TRACE("TcpServer::recv: Error: accept\n");
                state = STT_OPEN;
                return RES_NOK;
            }

            TRACE("TcpServer::recv: connection accepted\n");
            
            state = STT_ACTIVE;

            // Avoid break to execute the read if an active connection is established

        case STT_ACTIVE:

            res = ::recv(connFd, buffer, bufferSz, 0);
            if (res > 0) {
                return res;
            } else {
            	TRACE("TcpServer::recv: connection closed\n");
                ::close(connFd);
            	connFd = -1;
                state = STT_OPEN;
                return res;
                /* 
                if (res == 0) { // Close connection
                    TRACE("TcpServer::recv: connection closed\n");
                    ::close(connFd);
                    connFd = -1;
                    state = STT_OPEN;
                    return res;
                } else { // Close socket
                    TRACE("TcpServer::recv: Error: recv\n");
                    close();
                    return res;
                }
                */
            }

        default:
            return RES_NOK;

    }

    
}

int TcpServer::send(const void *buffer, size_t bufferSz) {
    
    if (state == STT_ACTIVE) {
        int res = ::send(connFd, buffer, bufferSz, 0);
        return res;
    } else {
        TRACE("TcpServer::send: Error: send: connection inactive\n");
        return RES_NOK;
    }
}
