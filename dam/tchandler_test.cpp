//
//  tchandler_test.cpp
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

int TcHandler::execConnTst(Header *tcHeader) {
    
    sendTcRx(tcHeader, TC_RX_OK);
    
    if (g_ctrlServer.getState() == TcpServer::STT_ACTIVE) {
    
        static const size_t buffSz = sizeof(Header)+sizeof(Data_ConnTst);
        uint8_t buff[buffSz];

        memset(buff, 0, buffSz);

        Header* header = (Header*)buff;
        header->apid     = Header::CLASS_TM + (uint16_t)g_configInfo.damApid;
        header->sequence = Header::GROUP_STAND_ALONE + (uint16_t)g_systemInfo.getPacketCount();
        header->type     = Data_ConnTst::TYPE;
        header->subType  = Data_ConnTst::SUB_TYPE;
        header->size     = sizeof(Data_ConnTst);

        Data_ConnTst* data = (Data_ConnTst*)(buff+sizeof(Header));
        data->_p8[0] = 0x80;
        data->_p8[1] = 0x09;
        data->_p8[2] = 0xA0;
        data->_p8[3] = 0x0B;
        data->_p8[4] = 0xC0;
        data->_p8[5] = 0x0D;
        data->_p8[6] = 0xE0;
        data->_p8[7] = 0x0F;

        //data->encode();
        header->encode();
    
        // TODO: handle return errors
        g_ctrlServer.send(buff, buffSz);
        
    }
    
    sendTcExec(tcHeader, TC_EX_OK);
    
    return 0;
    
}
