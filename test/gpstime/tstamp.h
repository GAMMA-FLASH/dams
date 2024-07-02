#ifndef __TSTAMP_H__
#define __TSTAMP_H__

#include <cstdint>
#include <pthread.h>
    
class TimeStamp {

public:

	// APID
    enum {
        TS_VALID 	= 0x00,
        TS_NOPPS 	= 0x80,
        TS_NOUART 	= 0x40,
        TS_OVFLOW   = 0x01
    } TimeSts;
    
    // Time tag data
	typedef union {
    	uint8_t _p8[24];
    	uint16_t _p16[12];
    	uint32_t _p32[6];
    	struct __attribute__((packed)) {
        	struct timespec ts; 	// 1-2, 2 x 32
    		uint32_t hh;			// 3
    		uint32_t mm;			// 4
    		uint32_t ss;			// 5
    		uint32_t us;			// 6
    	};
	} CurrentTime;
	
	typedef union {
		uint8_t _p8[44];
        uint16_t _p16[22];
        uint32_t _p32[11];
		struct __attribute__((packed)) {
    		uint16_t ppsSliceNo; // 0
    		uint8_t year;
    		uint8_t month;	
    		uint8_t day;		// 1
    		uint8_t hh;
    		uint8_t mm;
    		uint8_t ss;
    		uint32_t us;		// 2
		};
	} AbsoluteTime;
	
	TimeStamp();
	~TimeStamp();
	
	int init();
	void destroy();
	
	uint32_t read(CurrentTime *currTime);
	void computeAbsoluteTime(const struct timespec *ts, CurrentTime *currTime, AbsoluteTime *absTime);
	
	//uint32_t getAbsTime(const struct timespec *ts, TimeAbs *t);
	//uint32_t getAbsTime(TimeInfo *raw, const struct timespec *ts, TimeAbs *t);
	
	/*
	void print(const struct timespec *ts);
	void read(const struct timespec *ts, TimeInfo *tinfo);
	*/
	
protected:
	
private:

	bool threadStarted;
    pthread_t ppsAcqThreadInfo;
    pthread_t ggaAcqThreadInfo;	
	
};

#endif /* __TSTAMP_H__ */
