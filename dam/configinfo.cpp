//
//  configinfo.cpp
//  DAM_xc
//
//  Created by Alessio Aboudan on 19/02/21.
//

#include "config.h"
#include "trace.h"

#include "pugixml.hpp"

#include "configinfo.h"

using namespace std;
using namespace pugi;

ConfigInfo::ConfigInfo() {
    
    damApid = DAM_APID;
   
   	damRunID = DAM_RUN_ID;
    damSessionID = DAM_SESSION_ID;
    damConfigID = DAM_CONFIG_ID;
    
    cfgMonitorPeriodSecs = CFG_MONITOR_PERIOD_SECS;
     
    oscEqLevel 		= OSC_EQ_LEVEL;
    oscDecimation 	= OSC_DECIMATION;
    oscTrigSource 	= OSC_TRIG_SOURCE;
    oscTrigThresh 	= OSC_TRIG_THRESH;
    oscTrigHyst 	= OSC_TRIG_HYST;
    oscTrigDelay 	= OSC_TRIG_DELAY;
    oscTrigDebounce = OSC_TRIG_DEBOUNCE;
     
}

int ConfigInfo::init() {
	
	// Load run id
	int res = loadCounter(DAM_RUN_FNAME, &damRunID);
	if (res == 0) {
		damRunID++;
	}
	res = saveCounter(DAM_RUN_FNAME, damRunID);
	if (res < 0) {
		return -1;
	}
	
	// Load configuration data
	res = loadConfig(DAM_CONFIG_FNAME);
	if (res < 0) {
		res = saveConfig(DAM_CONFIG_FNAME);
		if (res < 0) {
			return -1;
		}
		printf("Save default configuration\n");
	}
	
	printf("Application identification\n");
	printf("         APID ID %8d\n", damApid);
	printf("          Run ID %8d\n", damRunID);
	printf("      Session ID %8d\n", damSessionID);
	printf("Configuration ID %8d\n", damConfigID);
	
	return 0; 

}

int ConfigInfo::loadCounter(const char* fname, int* count) {

	if (fname) {
	
		FILE *pfile = fopen(fname, "r");
        if (pfile != NULL) {
            fscanf(pfile, "%d", count);
            fclose(pfile);
            return 0;
        } else {
            TRACE("DataStore::loadCounter: Error: Open %s for reading failed\n", fname);
            perror("fopen: ");
            return -1;
        }
	
	} else {
        TRACE("ConfigInfo::loadCounter: Error: File name not specified\n");
        return -1;
    }

}
 
int ConfigInfo::saveCounter(const char* fname, int count) {

	if (fname) {
	
		FILE *pfile = fopen(fname, "w");
        if (pfile != NULL) {
            fprintf(pfile, "%06d\n", count);
            fclose(pfile);
            return 0;
        } else {
            TRACE("DataStore::saveCounter: Error: Open %s for writing failed\n", fname);
            perror("fopen: ");
            return -1;
        }
	
	} else {
        TRACE("ConfigInfo::loadCounter: Error: File name not specified\n");
        return -1;
    }

}
 
int ConfigInfo::loadConfig(const char *fname) {
    
    if (fname) {
        
        xml_document doc;
        
        xml_parse_result res = doc.load_file(fname);
        if (res.status) {
            TRACE("ConfigInfo::load: Error: %s\n", res.description());
            return -1;
        }
            
        // Read parameters
        
        xml_node dam = doc.child("DAM");
        if (dam) {
        	damApid = dam.attribute("apid").as_int();
        	damSessionID = dam.attribute("sessionID").as_int();
        	damConfigID = dam.attribute("configID").as_int();
        }
        
        xml_node cfg = doc.child("Configuration");
        if (cfg) {
        	cfgMonitorPeriodSecs = cfg.attribute("monitorPeriodSecs").as_int();
        }
        
        xml_node osc = doc.child("Oscilloscope");
        if (osc) {
        	oscEqLevel = osc.attribute("eqLevel").as_int();
        	oscDecimation = osc.attribute("decimation").as_int();
        	oscTrigSource = osc.attribute("trigSource").as_int();
        	oscTrigThresh = osc.attribute("trigThresh").as_int();
        	oscTrigHyst = osc.attribute("trigHyst").as_int();
        	oscTrigDelay = osc.attribute("trigDelay").as_int();
        	oscTrigDebounce = osc.attribute("trigDebounce").as_int();
        }
        
        return 0;
        
    } else {
        TRACE("ConfigInfo::load: Error: File name not specified\n");
        return -1;
    }
    
}

int ConfigInfo::saveConfig(const char *fname) {
    
    xml_document doc;
    
    if (fname) {
        
        xml_document doc;
        
        xml_node dam = doc.append_child("DAM");
        
        char str[16];
        sprintf(str, "%02d.%02d.%04d", ASW_VER, ASW_SUB, ASW_DEP);
        dam.append_attribute("version") = str;
        
        sprintf(str, "%02d", damApid);
        dam.append_attribute("apid") = str;
        
        sprintf(str, "%02d", damSessionID);
        dam.append_attribute("damSessionID") = str;
        
        sprintf(str, "%02d", damConfigID);
        dam.append_attribute("configID") = str;
        
        xml_node cfg = doc.append_child("Configuration");
        
        sprintf(str, "%04d", cfgMonitorPeriodSecs);
        cfg.append_attribute("monitorPeriodSecs") = str;
        
        xml_node osc = doc.append_child("Oscilloscope");
        
        sprintf(str, "%02d", oscEqLevel);
        osc.append_attribute("eqLevel") = str;
        
        sprintf(str, "%04d", oscDecimation);
        osc.append_attribute("decimation") = str;
        
        sprintf(str, "%02d", oscTrigSource);
        osc.append_attribute("trigSource") = str;
        
        sprintf(str, "%06d", oscTrigThresh);
        osc.append_attribute("trigThresh") = str;
        
        sprintf(str, "%06d", oscTrigHyst);
        osc.append_attribute("trigHyst") = str;
        
        sprintf(str, "%06d", oscTrigDelay);
        osc.append_attribute("trigDelay") = str;
        
        sprintf(str, "%06d", oscTrigDebounce);
        osc.append_attribute("trigDebounce") = str;
        
        doc.save_file(fname);

        return 0;
        
    } else {
        TRACE("ConfigInfo::save: Error: File name not specified\n");
        return -1;
    }
    
}
