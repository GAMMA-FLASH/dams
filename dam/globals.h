/*
 * globals.h
 *
 *  Created on: May 2, 2017
 *      Author: alessio
 */

#ifndef __GLOBALS_H__
#define __GLOBALS_H__

#include "configinfo.h"
#include "systeminfo.h"
#include "datastore.h"
#include "tcp.h"
#include "tchandler.h"
#include "waveacq.h"
#include "tstamp.h"

//--------------------------------------------------------------------------
// Configuration info
//--------------------------------------------------------------------------
extern ConfigInfo g_configInfo;

//--------------------------------------------------------------------------
// System info
//--------------------------------------------------------------------------
extern SystemInfo g_systemInfo;

//--------------------------------------------------------------------------
// System info
//--------------------------------------------------------------------------
extern DataStore g_dataStore;

//--------------------------------------------------------------------------
// Control server
//--------------------------------------------------------------------------
extern TcpServer g_ctrlServer;

//--------------------------------------------------------------------------
// TC handler
//--------------------------------------------------------------------------
extern TcHandler g_tcHandler;

//--------------------------------------------------------------------------
// GPS timestamp handling
//--------------------------------------------------------------------------
extern TimeStamp g_timeStamp;

//--------------------------------------------------------------------------
// Waveform acquisition
//--------------------------------------------------------------------------
extern WaveAcq g_waveAcq;

//--------------------------------------------------------------------------
// Main thread 
//--------------------------------------------------------------------------
extern pthread_t g_mainThreadInfo;

#endif // __GLOBALS_H__
