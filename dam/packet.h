//
//  packet.h
//  Packet
//
//  Created by Alessio Aboudan on 20/05/21.
//

#ifndef __PACKET_H__
#define __PACKET_H__

#include <cstdint>
#include <time.h>

#include "config.h"

#define TC_RX_OK 			0x00
#define TC_RX_ERR_WRONGSTT 	0xFF

#define TC_EX_OK 			0x00
#define TC_EX_ERR_RUPDFAIL 	0xFE
#define TC_EX_ERR_INITFAIL  0xFD

class Header {
    
public:
    
    static const uint16_t MAX_PACK_SIZE = 4096;
    static const uint16_t MAX_DATA_SIZE = 4084;
    
    // Constant pattern
    enum {
        START = 0x8D
    };
    
    // APID
    enum {
        CLASS_TC = 0x00,
        CLASS_TM = 0x80,
        CLASS_MASK = 0x80,
        SOURCE_MASK = 0x7F
    };
    
    // Sequence
    enum {
        GROUP_CONT = 0x0000,
        GROUP_FIRST = 0x4000,
        GROUP_LAST = 0x8000,
        GROUP_STAND_ALONE = 0xC000,
        GROUP_MASK = 0xC000,
        COUNT_MASK = 0x3FFF
    };
    
    // Header data
    union {
        uint8_t _p8[12];
        uint16_t _p16[6];
        uint32_t _p32[3];
        struct __attribute__((packed)) {
            uint8_t start;
            uint8_t apid;
            uint16_t sequence;
            uint8_t type;
            uint8_t subType;
            uint16_t size;
            uint32_t crc;
        };
    };
    
    void encode();
    int decode();

    void print();
    
};

class Data_TcRx {
    
public:
    
    static const uint8_t TYPE = 0x01;
    static const uint8_t SUB_TYPE = 0x01;
    
    // Header data
    union {
        uint8_t _p8[4];
        uint16_t _p16[2];
        uint32_t _p32[1];
        struct __attribute__((packed)) {
            uint8_t err;
            uint8_t apid;
            uint16_t sequence;
        };
    };
    
};

class Data_TcExec {
    
public:
    
    static const uint8_t TYPE = 0x01;
    static const uint8_t SUB_TYPE = 0x02;
    
    // Header data
    union {
        uint8_t _p8[4];
        uint16_t _p16[2];
        uint32_t _p32[1];
        struct __attribute__((packed)) {
            uint8_t err;
            uint8_t apid;
            uint16_t sequence;
        };
    };

};

class Data_Hk {
    
public:
    
    static const uint8_t TYPE = 0x03;
    static const uint8_t SUB_TYPE = 0x01;
    
    // Header data
    union {
        uint8_t _p8[8];
        uint16_t _p16[4];
        uint32_t _p32[2];
        struct __attribute__((packed)) {
            uint8_t state;
            uint8_t flags;
            uint8_t spare0;
            uint8_t spare1;
            uint32_t waveCount;
        };
    };
    
};

class Data_ConnTst {
    
public:
    
    static const uint8_t TYPE = 0x11;
    static const uint8_t SUB_TYPE = 0x01;
    
    // Header data
    union {
        uint8_t _p8[8];
        uint16_t _p16[4];
        uint32_t _p32[2];
    };
    
};

class Data_StartAcq {

public:

	static const uint8_t TYPE = 0xA0;
    static const uint8_t SUB_TYPE = 0x04;
    
    // Header data
    union {
        uint8_t _p8[12];
        uint16_t _p16[6];
        uint32_t _p32[3];
        struct __attribute__((packed)) {
            uint8_t source;
            uint8_t spare0;
            uint8_t spare1;
            uint8_t spare2;
            uint32_t maxWaveNo;
            uint32_t waitUsecs;
        };
    };
    
};

class Data_WaveHeader {
    
public:
    
    static const uint8_t TYPE = 0xA1;
    static const uint8_t SUB_TYPE = 0x01;
    
    // Header data
    union {
        uint8_t _p8[36];
        uint16_t _p16[18];
        uint32_t _p32[9];
        struct __attribute__((packed)) {
        	uint32_t runID;
        	uint32_t sessionID;
        	uint32_t configID;
            struct timespec ts;
            uint32_t dec;
            uint32_t currOff;
            uint32_t trigOff;
            uint32_t size;
        };
    };
    
};

class Data_WaveData {
    
public:
    
    static const uint8_t TYPE = 0xA1;
    static const uint8_t SUB_TYPE = 0x02;
    
    // Header data
    union {
        uint8_t _p8[4*U32_X_PACKET];
        uint16_t _p16[2*U32_X_PACKET];
        uint32_t _p32[U32_X_PACKET];
    };
    
};

#endif // __PACKET_H__
