/*
 * globals.c
 *
 *  Created on: May 2, 2017
 *      Author: alessio
 */

#include "config.h"

#include "globals.h"

ConfigInfo g_configInfo;
SystemInfo g_systemInfo;
DataStore g_dataStore;
TcpServer g_ctrlServer;
TcHandler g_tcHandler;
TimeStamp g_timeStamp;
WaveAcq g_waveAcq;
pthread_t g_mainThreadInfo;
