//
//  config.h
//  DAM_xc
//
//  Created by Alessio Aboudan on 19/02/21.
//

#ifndef __CONFIG_H__
#define __CONFIG_H__

#include "osc_fpga.h"

//--------------------------------------------------------------------------
// Software version
//--------------------------------------------------------------------------
#define ASW_VER 2
#define ASW_SUB 4
#define ASW_DEP 3

//--------------------------------------------------------------------------
// Appplication identification
//--------------------------------------------------------------------------

// Fixed value to identifiy each RP
#define DAM_APID 1

// Incremented at each startup and when the acq. is started
#define DAM_RUN_ID 0
#define DAM_RUN_FNAME "RUN_ID.txt"

//--------------------------------------------------------------------------
// Configuration 
//--------------------------------------------------------------------------
#define DAM_SESSION_ID 0
#define DAM_CONFIG_ID 0
#define DAM_CONFIG_FNAME "CONFIG.xml"

//--------------------------------------------------------------------------
// Path for data storage
//--------------------------------------------------------------------------
#define DATA_STORAGE_PATH "./DATA"

//--------------------------------------------------------------------------
// Control server
//--------------------------------------------------------------------------
#define TCP_CTRL_PORT 1234

//--------------------------------------------------------------------------
// Monitor loop
//--------------------------------------------------------------------------
#define CFG_MONITOR_PERIOD_SECS 5
#define CFG_SEND_WFORM			true
#define CFG_SAVE_WFORM			false
#define CFG_SAVE_WFORM_NO		10000

//--------------------------------------------------------------------------
// Waveform FIFO
//--------------------------------------------------------------------------
#define OSC_FPGA_SIG_LEN   (16*1024)	// 16384 samples
#define FIFO_BUFF_NO 		6
#define FIFO_BUFF_SZ 		8204        // Buffer size in terms of unit32 (8192 pairs of samples + 12 int x header)
#define U32_X_PACKET 		1020		// Number of uint32 for each packet

//--------------------------------------------------------------------------
// OSC classic
//--------------------------------------------------------------------------
#define OSC_EQ_LEVEL		OSC_FPGA_EQ_LV
#define OSC_DECIMATION 		OSC_FPGA_DEC1
#define OSC_TRIG_SOURCE 	OSC_FPGA_TSRC_CHA_POS
#define OSC_TRIG_THRESH 	128
#define OSC_TRIG_HYST 		50
#define OSC_TRIG_DELAY 		1024
#define OSC_TRIG_DEBOUNCE 	10

//--------------------------------------------------------------------------
// Data store
//--------------------------------------------------------------------------
#define DS_SAVE_WFORM		0
#define DS_WFORM_NO			10000
#endif // __CONFIG_H__
