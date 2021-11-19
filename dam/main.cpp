//
//  main.cpp
//  DAM_xc
//
//  Created by Alessio Aboudan on 19/02/21.
//

#include <cstdio>
#include <cstdlib>
#include <string.h>
#include <fcntl.h>
#include <signal.h>
#include <pthread.h>
#include <sched.h>
#include <semaphore.h>
#include <unistd.h>

#include "config.h"
#include "trace.h"

#include "globals.h"

#include "tchandler.h"
#include "packet.h"

// Send periodic HK accroding to the configuration
void sendPeriodicHk();

int main(int argc, const char * argv[]) {
    
    printf("Data Acquisition Module (%02d.%02d.%04d)\n", ASW_VER, ASW_SUB, ASW_DEP);
    
    //--------------------------------------------------------------------------
    // Config info
    //--------------------------------------------------------------------------
    int res = g_configInfo.init();
    if (res < 0) {
        printf("Error: Init config info\n");
        exit(EXIT_FAILURE);
    }
    
    //--------------------------------------------------------------------------
    // System info
    //--------------------------------------------------------------------------
    res = g_systemInfo.init();
    if (res < 0) {
        printf("Error: Init system info\n");
        exit(EXIT_FAILURE);
    }
    
    //--------------------------------------------------------------------------
    // Data store
    //--------------------------------------------------------------------------
    res = g_dataStore.init();
    if (res < 0) {
        printf("Error: Init data store\n");
        exit(EXIT_FAILURE);
    }
    
    // TODO: copy the config.xml in the save directory?
    
    //--------------------------------------------------------------------------
    // Control server
    //--------------------------------------------------------------------------
    res = g_ctrlServer.open(TCP_CTRL_PORT);
    if (res < 0) {
        printf("Error: Opening control server\n");
        exit(EXIT_FAILURE);
    }
    
    //--------------------------------------------------------------------------
    // Start TC handler thread
    //--------------------------------------------------------------------------
    res = g_tcHandler.init();
    if (res < 0) {
        printf("Error: Init TC handler\n");
        exit(EXIT_FAILURE);
    }
    
    //--------------------------------------------------------------------------
    // Enter low priority periodic monitoring task
    //--------------------------------------------------------------------------
    
    printf("Enter monitor cycle\n");
    
    // Init the ID of the main thread, the data acquisition can send
    // the SIGINT to terminate the whole process if needed
    g_mainThreadInfo = pthread_self();
        
    // Set signals to be blocked
    sigset_t sigMask;
    sigemptyset(&sigMask);
    //sigaddset(&sigMask, SIGRTMIN);
    sigaddset(&sigMask, SIGALRM);
    sigaddset(&sigMask, SIGINT);
    sigaddset(&sigMask, SIGUSR1);
    pthread_sigmask(SIG_BLOCK, &sigMask, NULL);

    // Set signals to be handled in this thread
    sigemptyset(&sigMask);
    sigaddset(&sigMask, SIGALRM);
    sigaddset(&sigMask, SIGINT);
    sigaddset(&sigMask, SIGUSR1);

    // Arm the alarm
    alarm(g_configInfo.cfgMonitorPeriodSecs);
    
    // INFINITE LOOP
    bool run = 1;
    while (run) {
        
        int sigNo;
        sigwait(&sigMask, &sigNo);

        switch(sigNo) {

            case SIGINT:
                run = 0;
                break;
                
            case SIGUSR1:
            	g_waveAcq.destroy();
            	TRACE("Stop wavefomr acquisition: acq. %8d sent %8d\n", g_systemInfo.totAcqWaveCount, g_systemInfo.totSentWaveCount);
            	break;

            case SIGALRM:
            
                // Collect HK data and send to the remote server
                g_tcHandler.sendHk();
                
                alarm(g_configInfo.cfgMonitorPeriodSecs);
                break;

        }

    }
    
    //-----------------------------------------------------------------------------
    // End
    //-----------------------------------------------------------------------------
    printf("End\n");
    
    return 0;
}
