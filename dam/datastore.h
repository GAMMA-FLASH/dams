//
//  datastore.h
//  DAM_xc
//
//  Created by Alessio Aboudan on 26/02/21.
//

#ifndef __DATASTORE_H__
#define __DATASTORE_H__

#include <cstdint>

#define DS_MAX_NAME_LEN 512 

class DataStore {
  
public:
    
    DataStore();
    ~DataStore();
    
    int init();
    
    int openFile();
    int save(void *buff, uint32_t buffSz);
    int closeFile();
    
protected:
    
    char path[DS_MAX_NAME_LEN];
    FILE *pFile;
    
private:
    
};

#endif // __DATASTORE_H__
