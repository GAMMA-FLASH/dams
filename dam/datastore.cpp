//
//  datastore.cpp
//  DAM_xc
//
//  Created by Alessio Aboudan on 26/02/21.
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/types.h>

#include "config.h"
#include "trace.h"

#include "globals.h"

#include "datastore.h"

using namespace std;

DataStore::DataStore() {
    
    memset(path, 0, DS_MAX_NAME_LEN);
    
    pFile = 0;
    
}

DataStore::~DataStore() {

}

int DataStore::init() {

	if (pFile) {
		fclose(pFile);
		pFile = 0;
	}
    
    // Check if a directory exists
    struct stat st = {0};
    if (stat(DATA_STORAGE_PATH, &st) == -1) {
        TRACE("DataStore::init: Create data directory\n");
        mkdir(DATA_STORAGE_PATH, 0700);
    } 
        
    // fpath prefix
    sprintf(path, DATA_STORAGE_PATH "/%06d_", g_configInfo.damRunID);

    // fpath time field
    time_t ltime;
    ltime = time(NULL);
        
    struct tm *tmp;
    tmp = localtime(&ltime);
        
    char ftime[DS_MAX_NAME_LEN];
    strftime(ftime, sizeof(ftime), "%Y%m%d%H%M%S", tmp);

    // fpath
    strcat(path, ftime);

    TRACE("DataStore::init: Current path %s\n", path);

    // Create output directory
    mkdir(path, 0700);

    return 0;
    
}

int DataStore::openFile() {
	
	if (!pFile) {
	
		// Create file name
		char fname[DS_MAX_NAME_LEN];
		
		sprintf(fname, "%s/%06d_", path, g_systemInfo.fileCount);
		
		// fpath time field
    	time_t ltime;
    	ltime = time(NULL);
        
    	struct tm *tmp;
    	tmp = localtime(&ltime);
        
    	char ftime[DS_MAX_NAME_LEN];
    	strftime(ftime, sizeof(ftime), "%Y%m%d%H%M%S", tmp);

    	// fpath
    	strcat(fname, ftime);
	
		TRACE("DataStore::openFile: Current file %s\n", fname);
	
		// Open file
		pFile = fopen(fname, "wb");
		
		g_systemInfo.fileCount++;
		
		return 0;
	
	} else {
		return -1;
	}

}

int DataStore::save(void *buff, uint32_t buffSz) {
	if (pFile) {
		// TODO: handle errors
		fwrite(buff, 1, buffSz, pFile);
		fflush(pFile);
		return 0;
	} else {
		return -1;
	}
	
}

int DataStore::closeFile() {
	if (pFile) {
		fclose(pFile);
		pFile = 0;
		return 0;
	} else {
		return -1;
	}
}
    

