//
//  tchandler_acq.cpp
//  DAM_xc
//
//  Created by Alessio Aboudan on 04/10/21.
//

#include <cstdio>
#include <cstdlib>
#include <string.h>

#include "config.h"
#include "trace.h"

#include "globals.h"

#include "tchandler.h"

int TcHandler::execStartAcq(Header *tcHeader) {
    
    // Check the status
    if (g_systemInfo.state == SystemInfo::STT_SERVICE) {
        
        sendTcRx(tcHeader, TC_RX_OK);
        
        usleep(100);
        
        // Read configuration params form the header
        Data_StartAcq* data = (Data_StartAcq*)((uint8_t*)tcHeader + sizeof(Header));
        g_systemInfo.source = data->source;
        g_systemInfo.maxWaveNo = data->maxWaveNo;
        g_systemInfo.waitUsecs = data->waitUsecs;
        
        // Clear trigger error flag
        g_systemInfo.flags &= ~((uint32_t)SystemInfo::FLG_TRG_ERR);
        
        TRACE("TcHandler::execStartAcq: source %d maxWaveNo %d waitUsecs %d\n", g_systemInfo.source, g_systemInfo.maxWaveNo, g_systemInfo.waitUsecs);
        
        // Increment the run ID
        g_configInfo.damRunID++;
        int res = g_configInfo.saveCounter(DAM_RUN_FNAME, g_configInfo.damRunID);
		if (res < 0) {
			sendTcExec(tcHeader, TC_EX_ERR_RUPDFAIL);
			return 0;
		}
		
		// Update counters
		g_systemInfo.acqWformCount = 0;
		g_systemInfo.sentWformCount = 0;
		g_systemInfo.savedWformCount = 0;
    	g_systemInfo.fileCount = 0;
		g_dataStore.init(); 
		
		TRACE("TcHandler::execStartAcq: run ID %d\n", g_configInfo.damRunID);
        
        res = g_waveAcq.init();
        
        usleep(100);
        
        if (res == 0) {
            sendTcExec(tcHeader, TC_EX_OK);
        } else {
            sendTcExec(tcHeader, TC_EX_ERR_INITFAIL);
        }
        
    } else {
        sendTcRx(tcHeader, TC_RX_ERR_WRONGSTT);
    }
    
    return 0;
    
}

int TcHandler::execStopAcq(Header *tcHeader) {
 
    if (g_systemInfo.state == SystemInfo::STT_ACQUISITION) {
        
        sendTcRx(tcHeader, TC_RX_OK);
        
        g_waveAcq.destroy();
        
        usleep(100);
        
        // Clear trigger error flag
        g_systemInfo.flags &= ~((uint32_t)SystemInfo::FLG_TRG_ERR);
        
        sendTcExec(tcHeader, TC_EX_OK);
        
    } else {
        sendTcRx(tcHeader, TC_RX_ERR_WRONGSTT);
    }
    
    return 0;
    
}
