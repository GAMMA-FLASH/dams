#include <cstdio>
#include <cstdlib>
#include <time.h>
#include <errno.h>

#include "config.h"
#include "trace.h"

#include "globals.h"

#include "hk_fpga.h"
#include "uart.h"

#include "tstamp.h"

#define TH_MINUTES 20

static uint32_t m_status;

static struct timespec m_pps_ts;
static struct timespec m_gga_ts;

static struct timespec m_tstamp_ts;
static int m_tstamp_hh = 0;
static int m_tstamp_mm = 0;
static int m_tstamp_ss = 0;
static int m_tstamp_us = 0;

pthread_mutex_t m_tstamp_lock;

static inline uint32_t delta_nsec(const struct timespec *t1, const struct timespec *t0) {
	uint32_t dsec = t1->tv_sec - t0->tv_sec;
	uint32_t dnsec = t1->tv_nsec - t0->tv_nsec;
	if (dsec > 0) {
		dnsec += 1000000000;
	}
	return dnsec; 
}

static inline void delta_time(const struct timespec *t1, const struct timespec *t0, struct timespec *dt) {
	dt->tv_sec = t1->tv_sec - t0->tv_sec;
	dt->tv_nsec = t1->tv_nsec - t0->tv_nsec;
	if (dt->tv_sec > 0) {
		dt->tv_sec -= 1;
		dt->tv_nsec += 1000000000;
	}
	if (dt->tv_nsec >= 1000000000) {
		dt->tv_sec += 1;
		dt->tv_nsec -= 1000000000;
	}
}

static inline int pps_wait() {
	for(int i = 0; i < 500000; i++) {
		if (g_hk_fpga_reg_mem->in_p & HK_FPGA_GPIO_BIT7) {
			clock_gettime(CLOCK_REALTIME, &m_pps_ts);
			return 0;
		} else {
			usleep(5);
		}
	}

	return -1;
}

void *ppsAcqThreadFcn(void *ptr) {
	
	sleep(1);
    
    for(;;) {
        int res = pps_wait();
        if (res == 0) { // PPS found wait till the next one
        	m_status &= ~(uint32_t)TimeStamp::TS_NOPPS;
			g_systemInfo.flags &= ~((uint32_t)SystemInfo::FLG_PPS_NOK);
        	usleep(750000);
        } else { // No signal/fix from PPS
        	m_status += (uint32_t)TimeStamp::TS_NOPPS;
			g_systemInfo.flags |= ((uint32_t)SystemInfo::FLG_PPS_NOK);
        	sleep(1);
        }
/*
	if (m_status) {
		g_systemInfo.flags |= (uint8_t)m_status;
	} else {
		g_systemInfo.flags &= ~(uint8_t)(TimeStamp::TS_NOPPS+TimeStamp::TS_NOUART);
	}
*/
    }
    
    // This point should never be reached
    return EXIT_SUCCESS;
    
}

static inline void gga_read() {

	if (g_uart_nbytes < 17) {
		return;
	}
	
	if (g_uart_buff[0] == '$') {
		
		if (g_uart_buff[1] == 'G') {
		
			if (g_uart_buff[2] == 'P' || g_uart_buff[2] == 'L' || g_uart_buff[2] == 'N') {
				
				if (g_uart_buff[3] == 'G') { // GGA
				
					if (g_uart_buff[4] == 'G') {
					
						if (g_uart_buff[5] == 'A') {
						
							clock_gettime(CLOCK_REALTIME, &m_gga_ts);
							
							uint32_t dnsec = delta_nsec(&m_gga_ts, &m_pps_ts);
            				
            				if (dnsec < 1000000000) {
								
								pthread_mutex_lock(&m_tstamp_lock);

								m_tstamp_ts.tv_sec = m_pps_ts.tv_sec;
								m_tstamp_ts.tv_nsec = m_pps_ts.tv_nsec;

								m_tstamp_hh = (uint32_t)(g_uart_buff[7]-'0')*10 + (uint32_t)(g_uart_buff[8]-'0');
								m_tstamp_mm = (uint32_t)(g_uart_buff[9]-'0')*10 + (uint32_t)(g_uart_buff[10]-'0');
								m_tstamp_ss = (uint32_t)(g_uart_buff[11]-'0')*10 + (uint32_t)(g_uart_buff[12]-'0');
								m_tstamp_us = (uint32_t)(g_uart_buff[14]-'0')*100000 + (uint32_t)(g_uart_buff[15]-'0')*10000 + (uint32_t)(g_uart_buff[16]-'0');
								
								time_t rawtime;
								struct tm *timeinfo;
    							time(&rawtime);
								timeinfo = localtime(&rawtime);
								int current_hour = timeinfo->tm_hour;
								int current_minute = timeinfo->tm_min;

								// Compare parsed time with system time
								int minute_difference = (m_tstamp_hh * 60 + m_tstamp_mm) - (current_hour * 60 + current_minute);
								int threshold_minutes = TH_MINUTES;  // Set the threshold range of minutes
								
								if (abs(minute_difference) > threshold_minutes) {
									printf("Error: System time is not within %d minutes of GNGGA time: current %d:%d ; gps %d:%d\n", threshold_minutes, current_hour, current_minute, m_tstamp_hh, m_tstamp_mm );
									g_systemInfo.flags |= ((uint32_t)SystemInfo::FLG_GPS_NOK);
								} else {
									printf("System time is within %d minutes of GNGGA time. difference %d min\n", threshold_minutes, minute_difference);
									g_systemInfo.flags &= ~((uint32_t)SystemInfo::FLG_GPS_NOK);
								}

								//printf("%02X %s\n", m_status, g_uart_buff);

								pthread_mutex_unlock(&m_tstamp_lock);
								
							} 
							else {
								printf("not checking time\n");
							}
							
						}
					
					}
					
				}
				
			}
		
		}
		
	}

}

void *ggaAcqThreadFcn(void *ptr) {
	
	sleep(1);
    
    for(;;) {
        int res = uart_read();
        if (res > 0) { // Search GGA sentence 
        	m_status &= ~(uint32_t)TimeStamp::TS_NOUART;
        	gga_read();
        } else {	// No data from UART
        	m_status += (uint32_t)TimeStamp::TS_NOUART;
        	sleep(1);
        }
    }
    
    // This point should never be reached
    return EXIT_SUCCESS;
    
}
	
TimeStamp::TimeStamp() {
	threadStarted = false;
	
}

TimeStamp::~TimeStamp() {
	if (threadStarted) {
        pthread_cancel(ggaAcqThreadInfo);
        pthread_join(ggaAcqThreadInfo, NULL);    
        pthread_cancel(ppsAcqThreadInfo);
        pthread_join(ppsAcqThreadInfo, NULL);
        uart_uninit();
        hk_fpga_uninit();
    }
}

int TimeStamp::init() {

	m_status = TS_NOPPS + TS_NOUART;

	pthread_mutex_init(&m_tstamp_lock, NULL);

	int res = hk_fpga_init();
    if (res < 0) {
		fprintf(stderr, "TimeStamp::init: Error: hk_fpga_init() failed\n");
		return -1;
	}
	
	res = uart_init();
	if (res < 0) {
		fprintf(stderr, "TimeStamp::init: Error: uart_init() failed\n");
		hk_fpga_uninit();
		return -1;
	}

	res = pthread_create(&ppsAcqThreadInfo, NULL, ppsAcqThreadFcn, this);
	if (res < 0) {
		fprintf(stderr, "TimeStamp::init: Error: pps acquisition thread creation failed\n");
		uart_uninit();
        hk_fpga_uninit();
        return -1;
	}
	    
    res = pthread_create(&ggaAcqThreadInfo, NULL, ggaAcqThreadFcn, this);
    if (res < 0) {
		fprintf(stderr, "TimeStamp::init: Error: gga sentence acquisition thread creation failed\n");
		pthread_cancel(ppsAcqThreadInfo);
    	pthread_join(ppsAcqThreadInfo, NULL);
		uart_uninit();
        hk_fpga_uninit();
        return -1;
	}
    
    threadStarted = true;
	
	return 0;
   
}

void TimeStamp::destroy() {

	 if (threadStarted) {
    
        pthread_cancel(ggaAcqThreadInfo);
        pthread_join(ggaAcqThreadInfo, NULL);
        
        pthread_cancel(ppsAcqThreadInfo);
        pthread_join(ppsAcqThreadInfo, NULL);
        
        uart_uninit();
        
        hk_fpga_uninit();

        threadStarted = false;
        
    }

}

uint32_t TimeStamp::read(CurrentTime *currTime) {

	pthread_mutex_lock(&m_tstamp_lock);
	
	if (m_status == 0x00) {
		currTime->ts.tv_sec = m_tstamp_ts.tv_sec;
		currTime->ts.tv_nsec = m_tstamp_ts.tv_nsec;
		currTime->hh = m_tstamp_hh;
		currTime->mm = m_tstamp_mm;
		currTime->ss = m_tstamp_ss;
		currTime->us = m_tstamp_us;
	}
	
	pthread_mutex_unlock(&m_tstamp_lock);
	
	return m_status;

}

void TimeStamp::computeAbsoluteTime(const struct timespec *ts, CurrentTime *currTime, AbsoluteTime *absTime) {

	struct timespec delta_ts;
	delta_time(ts, &currTime->ts, &delta_ts);
	
	absTime->ppsSliceNo = (uint16_t)delta_ts.tv_sec;
	absTime->hh = currTime->hh;
	absTime->mm = currTime->mm;
	absTime->ss = currTime->ss + (uint32_t)delta_ts.tv_sec;
	absTime->us = currTime->us + (uint32_t)delta_ts.tv_nsec/1000;
	
	// Get year/month/day
	time_t timer; 
	time(&timer); 
	struct tm* tm_info = localtime(&timer);
    absTime->year = tm_info->tm_year;
	absTime->month = tm_info->tm_mon;
	absTime->day = tm_info->tm_mday;; 
	
}

/*
void TimeStamp::print(const struct timespec *ts) {

	pthread_mutex_lock(&m_tstamp_lock);
	
	struct timespec delta_ts;
	delta_time(ts, &m_tstamp_ts, &delta_ts);
	
	printf("Current Time\n");
	printf("PPS %lld.%.9ld\n", (long long)m_tstamp_ts.tv_sec, m_tstamp_ts.tv_nsec);
    printf("CUR %lld.%.9ld\n", (long long)ts->tv_sec, ts->tv_nsec);
    printf(" DT %lld.%.9ld\n", (long long)delta_ts.tv_sec, delta_ts.tv_nsec);
    
    printf("%02d%02d%02d.%06d\n", m_tstamp_hh, m_tstamp_mm, m_tstamp_ss , m_tstamp_us);
    printf("%02d%02d%02d.%06d\n", m_tstamp_hh, m_tstamp_mm, m_tstamp_ss + (uint32_t)delta_ts.tv_sec, m_tstamp_us + (uint32_t)delta_ts.tv_nsec/1000);

	pthread_mutex_unlock(&m_tstamp_lock);

}

void TimeStamp::read(const struct timespec *ts, TimeInfo *tinfo) {

	pthread_mutex_lock(&m_tstamp_lock);
	
	struct timespec delta_ts;
	delta_time(ts, &m_tstamp_ts, &delta_ts);
	
	if (delta_ts.tv_sec > 10) {
		m_status = TS_NOPPS + TS_NOUART;
	}

	tinfo->timeSts = m_status;
	
	if (m_status == 0x00) {
	
		tinfo->timeSts = m_status;
		tinfo->ppsSliceNo = (uint8_t)delta_ts.tv_sec;
		tinfo->hh = m_tstamp_hh;
		tinfo->mm = m_tstamp_mm;
		tinfo->ss = m_tstamp_ss + (uint32_t)delta_ts.tv_sec;
		tinfo->usec = m_tstamp_us + (uint32_t)delta_ts.tv_nsec/1000;
		
		pthread_mutex_unlock(&m_tstamp_lock);
		
		// Get year/month/day
		time_t timer; 
		time(&timer); 
		struct tm* tm_info = localtime(&timer);
        tinfo->year = tm_info->tm_year;
		tinfo->month = tm_info->tm_mon;
		tinfo->day = tm_info->tm_mday;; 
		
	} else {
		
		pthread_mutex_unlock(&m_tstamp_lock);
		
	}

}

*/
