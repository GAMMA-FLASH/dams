//
//  main.cpp
//  gpstime
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
#include <cstdint>
#include <termios.h> 
#include <errno.h>

#include "tstamp.h"


/*
static void get_current_time() {
	
	pthread_mutex_lock(&m_tstamp_lock);
	
	struct timespec curr_ts;
	clock_gettime(CLOCK_REALTIME, &curr_ts);
	
	struct timespec delta_ts;
	delta_timespec(&delta_ts, &curr_ts, &m_tstamp_ts);
	
	printf("Current Time\n");
	printf("PPS %lld.%.9ld\n", (long long)m_tstamp_ts.tv_sec, m_tstamp_ts.tv_nsec);
    printf("CUR %lld.%.9ld\n", (long long)curr_ts.tv_sec, curr_ts.tv_nsec);
    printf(" DT %lld.%.9ld\n", (long long)delta_ts.tv_sec, delta_ts.tv_nsec);
    
    pthread_mutex_unlock(&m_tstamp_lock);
    
    printf("%02d%02d%02d.%06d\n", m_tstamp_hh, m_tstamp_mm, m_tstamp_ss + (uint32_t)delta_ts.tv_sec, m_tstamp_us + (uint32_t)delta_ts.tv_nsec/1000);

}

*/


int main(int argc, const char * argv[]) {
    
    printf("Test accurate time tagging with GPS\n");
    
    TimeStamp tstamp;
    int res = tstamp.init();
    if (res < 0) {
    	return EXIT_FAILURE;
    }

    // Init the ID of the main thread, the data acquisition can send
    // the SIGINT to terminate the whole process if needed
    //g_mainThreadInfo = pthread_self();
        
    // Set signals to be blocked
    sigset_t sigMask;
    sigemptyset(&sigMask);
    //sigaddset(&sigMask, SIGRTMIN);
    sigaddset(&sigMask, SIGALRM);
    sigaddset(&sigMask, SIGINT);
    pthread_sigmask(SIG_BLOCK, &sigMask, NULL);

    // Set signals to be handled in this thread
    sigemptyset(&sigMask);
    sigaddset(&sigMask, SIGALRM);
    sigaddset(&sigMask, SIGINT);

    // Arm the alarm
    alarm(1);
    
    // INFINITE LOOP
    bool run = 1;
    while (run) {
        
        int sigNo;
        sigwait(&sigMask, &sigNo);

        switch(sigNo) {

            case SIGINT:
                run = 0;
                break;

            case SIGALRM:
            	
                alarm(2);
                
                struct timespec ts;
				clock_gettime(CLOCK_REALTIME, &ts);
				
				TimeStamp::CurrentTime curTime;
				uint32_t sts = tstamp.read( &curTime);

				TimeStamp::AbsoluteTime absTime;
				tstamp.computeAbsoluteTime(&ts, &curTime, &absTime);
				
				printf("%02X %02d %04d %02d %02d %02d %02d %02d %06d\n", sts, absTime.ppsSliceNo, absTime.year+1900, absTime.month, absTime.day, absTime.hh, absTime.mm, absTime.ss, absTime.us);
				
				//tstamp.print(&ts);
				
                break;

        }

    }
    
    //-----------------------------------------------------------------------------
    // End
    //-----------------------------------------------------------------------------
    printf("End\n");
    
    return EXIT_SUCCESS;
}
