//
//  configinfo.h
//  DAM_xc
//
//  Created by Alessio Aboudan on 19/02/21.
//

#ifndef __CONFIGINFO_H__
#define __CONFIGINFO_H__

#include <cstdio>

class ConfigInfo {
    
public:
    ConfigInfo();
    
    int init();
     
    int loadCounter(const char* fname, int* count);
    int saveCounter(const char* fname, int count);
    
    int loadConfig(const char* fname);
    int saveConfig(const char* fname);
    
    void print();
    
    int damApid;
    
    int damRunID;
    int damSessionID;
    int damConfigID;
    
    int cfgMonitorPeriodSecs;
    bool cfgSendWform;
    bool cfgSaveWform;
    int cfgSaveWformNo;
    
    int oscEqLevel;
    int oscDecimation;
    int oscTrigSource;
    int oscTrigThresh;
    int oscTrigHyst;
    int oscTrigDelay;
    int oscTrigDebounce;
    
    
    
};

#endif // __CONFIGINFO_H__
