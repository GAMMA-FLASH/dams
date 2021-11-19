//
//  datastore.h
//  DAM_xc
//
//  Created by Alessio Aboudan on 26/02/21.
//

#ifndef __DATASTORE_H__
#define __DATASTORE_H__

#include <cstdint>

#define DS_MAX_NAME_LEN 256

class DataStore {
  
public:
    
    DataStore();
    
    int init();
    
protected:
    
    char path[DS_MAX_NAME_LEN];
    
private:
    
};

#endif // __DATASTORE_H__
