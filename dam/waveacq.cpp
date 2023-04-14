//
//  waveacq.cpp
//  DAM_xc
//
//  Created by Alessio Aboudan on 04/10/21.
//

#include <cstdio>
#include <cstdlib>
#include <unistd.h>
#include <string.h>

#include <signal.h>
#include <pthread.h>

#include "config.h"
#include "trace.h"

#include "globals.h"

#include "fifo.h"
#include "osc_fpga.h"

#include "waveacq.h"

// Waveform FIFO
static uint32_t m_fifo_buff[FIFO_BUFF_NO*FIFO_BUFF_SZ];
static Fifo m_fifo(FIFO_BUFF_NO, FIFO_BUFF_SZ, m_fifo_buff);

// Stub function
void *testAcqThreadFcn(void *ptr) {
    
    TRACE("WaveAcq::testAcqThreadFcn: started\n");
    
    // Load the test waveform from file
    uint32_t* wform[FIFO_BUFF_SZ];
    FILE* pFile = fopen("testwaveform.bin","rb");
    fread (wform, 4, FIFO_BUFF_SZ, pFile);
    fclose(pFile);
    
    sleep(5);
    
    for(;;) {
        
        struct timespec ts;
        clock_gettime(CLOCK_REALTIME, (struct timespec*)&ts);
        
        uint32_t* buff;
        m_fifo.pushGet(&buff);
        
        // Copy the waveform
        memcpy(buff, wform, FIFO_BUFF_SZ*4);
        
        // Overwrite timestamp
        buff[0] = (uint32_t)ts.tv_sec;
        buff[1] = (uint32_t)ts.tv_nsec;
        
        m_fifo.pushRelease();
        
        //TRACE("WaveAcq::acqThreadFcn: push waveform\n");
        
        sleep(1);
        
    }
    
    // This point should never be reached
    return EXIT_SUCCESS;
    
}

// 32 bit aligned memcpy needed to access the memory mapped FPGA registers 
static inline void memcpy_32(volatile void *dst, volatile const void *src, size_t n) {
	volatile int *d = (volatile int*)dst;
	volatile const int *s = (volatile const int*)src;
	while(n--) {
		*d++ = *s++;
	}
}

// 32 bit aligned memcpy, convert u32 to u16 to min the memory footprint
static inline void memcpy_32_min(volatile void *dst, volatile const void *src, size_t n) {
	volatile int *d = (volatile int*)dst;
	volatile const int *s = (volatile const int*)src;
	while(n--) {
		if (n & 1) { // Copy the first number
			*d = *s++;
		} else { // Sum the second after the shift
			*d++ += *s++ << 16;
		}
	}
}

// Wform data
typedef union {
    uint8_t _p8[24];
    uint16_t _p16[12];
    uint32_t _p32[6];
    struct __attribute__((packed)) {
        struct timespec ts; // 2 x 32
        uint8_t tsts;
        uint8_t eql;
        uint16_t dec;
        uint32_t currOff;
        uint32_t trigOff;
        uint32_t size;
    };
} AcquisitionInfo;

// Full buffer
typedef struct {
	TimeStamp::CurrentTime currTime;
	AcquisitionInfo acqInfo;
	uint32_t data[OSC_FPGA_SIG_LEN/2];
} WaveformBuffer; // WaveformBuffer

void *acqThreadFcn(void *ptr) {
    
    TRACE("WaveAcq::acqThreadFcn: started\n");
    
    sleep(1);
    
    int res = osc_fpga_init();
    if (res < 0) {
		fprintf(stderr, "Error: osc_fpga_init() failed: terminate\n");
		return EXIT_SUCCESS;
	}
    
    sleep(1);
    
    // Make sure to have enought time to fill the buffer before the trigger
	int armDelayUsec = (OSC_FPGA_SIG_LEN - g_configInfo.oscTrigDelay)*8/(g_configInfo.oscDecimation*1000);
	if (armDelayUsec < 1) {
		armDelayUsec = 1;
	}
    
    printf("Configuration:\n");
	printf("       Eq. level: %6d\n", g_configInfo.oscEqLevel);
	printf("      Decimation: %6d\n", g_configInfo.oscDecimation);
	printf("    Trig. source: %6d\n", g_configInfo.oscTrigSource);
	printf(" Trig. threshold: %6d\n", g_configInfo.oscTrigThresh);
	printf("Trig. hysteresis: %6d\n", g_configInfo.oscTrigHyst);
	printf("     Trig. delay: %6d\n", g_configInfo.oscTrigDelay);
	printf("  Trig. debounce: %6d\n", g_configInfo.oscTrigDebounce);
	printf("    Max wave no.: %6d\n", g_systemInfo.maxWaveNo);
	printf("       Arm delay: %6d\n", armDelayUsec);	
    
    // 1. Reset
	osc_fpga_reset();
	
	// 2. Set filters
	osc_fpga_cha_set_filter(g_configInfo.oscEqLevel, 1);
	
	// 3. Set decimation
	osc_fpga_set_decimation(g_configInfo.oscDecimation);
	osc_fpga_set_averaging(0);
	
	// 4. Set trigger parameters
	osc_fpga_cha_set_trigger_par(g_configInfo.oscTrigThresh, g_configInfo.oscTrigHyst);
	osc_fpga_set_trigger_delay(g_configInfo.oscTrigDelay);
	osc_fpga_set_trigger_debounce(g_configInfo.oscTrigDebounce);
	
    // INFINITE LOOP
    for(;;) {
    	
    	// 5. Start writing into the FPGA memory
    	osc_fpga_arm_trigger();
    	
    	// 6. Wait to fill the pre-trigger part of the wform
    	usleep(armDelayUsec);
    	
    	// 7. Enable the trigger
    	osc_fpga_set_trigger_source(g_configInfo.oscTrigSource);
		
		// 8. Wait for an event
		// Sometime the trigger gets stucked so the wait is repeated a fixed number of times
		// (hardcoded in the function), in this case the function returns -1 and the 
		// trigger is armed again
		res = osc_fpga_wait_trigger(5);
		if (res == 0) {
		
			// Capture trigger time
			struct timespec trig_ts;
			clock_gettime(CLOCK_REALTIME, &trig_ts);
			
			// Get buffer
			WaveformBuffer *wformBuff = NULL;
			m_fifo.pushGet((uint32_t**)&wformBuff);
			
			// Get time stamp data
			uint32_t tsts = g_timeStamp.read(&wformBuff->currTime);
			
			// Fill packet header
			wformBuff->acqInfo.ts.tv_sec  	= trig_ts.tv_sec;
			wformBuff->acqInfo.ts.tv_nsec 	= trig_ts.tv_nsec;
			wformBuff->acqInfo.tsts 		= (uint8_t)tsts;
			wformBuff->acqInfo.eql 			= g_configInfo.oscEqLevel;
			wformBuff->acqInfo.dec 			= g_configInfo.oscDecimation;
			wformBuff->acqInfo.currOff 		= g_osc_fpga_reg_mem->wr_ptr_curr;
			wformBuff->acqInfo.trigOff 		= g_osc_fpga_reg_mem->wr_ptr_trig;
			wformBuff->acqInfo.size 		= OSC_FPGA_SIG_LEN;
			
			// Copy data
			memcpy_32_min(wformBuff->data, g_osc_fpga_cha_mem, OSC_FPGA_SIG_LEN);
			
			// Release buffer
			m_fifo.pushRelease();
			
			g_systemInfo.flags &= ~((uint32_t)SystemInfo::FLG_TRG_ERR);
			
			g_systemInfo.totAcqWformCount++;
			g_systemInfo.acqWformCount++;
			
			// Terminate the acquisition
			if (g_systemInfo.maxWaveNo > 0) {
				if (g_systemInfo.acqWformCount >= g_systemInfo.maxWaveNo) {
					
					// Wait to send all the data in the FIFO
					sleep(2);
					
					// Terminate acquisition
					pthread_kill(g_mainThreadInfo, SIGUSR1);
					
				}
			}
			
			// Wait time between two acquisitions
			if (g_systemInfo.waitUsecs) {
				usleep(g_systemInfo.waitUsecs);
			}
		
		} else {
			TRACE("WaveAcq::acqThreadFcn: trigger error [%d]\n", res);
			g_systemInfo.flags |= (uint32_t)SystemInfo::FLG_TRG_ERR;
		}
		
	}
    
    // This point should never be reached
    return EXIT_SUCCESS;
    
}

void *sendThreadFcn(void *ptr) {
    
    TRACE("WaveAcq::sendThreadFcn: started\n");
    
    for(;;) {
        
        uint32_t *buff = NULL;
        m_fifo.popGet(&buff);
        
        // The FIFO is empty
        if (buff == NULL) {
            sleep(1);
        } else {
        
        	TRACE("WaveAcq::sendThreadFcn: savedWformCount %d\n", g_systemInfo.savedWformCount);
        
        	if (g_configInfo.cfgSaveWform) {
        		if (g_systemInfo.savedWformCount == 0) {
        			g_dataStore.openFile();
        		}
        	}
        
            g_tcHandler.sendWaveform(buff, FIFO_BUFF_SZ);
            
            m_fifo.popRelease();
            
            if (g_configInfo.cfgSaveWform) {
            	if (g_systemInfo.savedWformCount >= (uint32_t)g_configInfo.cfgSaveWformNo) {
            		g_dataStore.closeFile();
            		g_systemInfo.savedWformCount = 0;
            	}
            }
            
            TRACE("WaveAcq::sendThreadFcn: pop release %6d\n", g_systemInfo.totSentWaveCount);
            
        }
        
    }
    
    // This point should never be reached
    return EXIT_SUCCESS;
    
}

WaveAcq::WaveAcq() {
    threadStarted = false;
}

WaveAcq::~WaveAcq() {
    if (threadStarted) {
        pthread_cancel(acqThreadInfo);
        pthread_join(acqThreadInfo, NULL);
        pthread_cancel(sendThreadInfo);
        pthread_join(sendThreadInfo, NULL);
    }
}

int WaveAcq::init() {

	m_fifo.init();
    
    int res = pthread_create(&sendThreadInfo, NULL, sendThreadFcn, this);
    if (res >= 0) {
    
    	void* (*pfun)(void*);
    	if (g_systemInfo.source == 0) {
    		pfun = acqThreadFcn;
    	} else {
    		pfun = testAcqThreadFcn;
    	}
        
        res = pthread_create(&acqThreadInfo, NULL, pfun, this);
        if (res >= 0) {
            
            threadStarted = true;
            
            // Change state
            g_systemInfo.state = SystemInfo::STT_ACQUISITION;
            
            // TODO: Send event
            
            return 0;
            
        } else {
            
            pthread_cancel(sendThreadInfo);
            pthread_join(sendThreadInfo, NULL);
            
        }
        
    }
    
    return -1;
    
}

int WaveAcq::destroy() {
    
    if (threadStarted) {
        
        pthread_cancel(acqThreadInfo);
        pthread_join(acqThreadInfo, NULL);
        
        pthread_cancel(sendThreadInfo);
        pthread_join(sendThreadInfo, NULL);
        
        threadStarted = false;
        
        // Change state
        g_systemInfo.state = SystemInfo::STT_SERVICE;
        
        // TODO: Send event
    
    }
    
    return 0;
    
}
