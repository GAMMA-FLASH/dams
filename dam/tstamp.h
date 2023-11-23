#ifndef TSTAMP_H
#define TSTAMP_H

#include <cstdint>
#include <ctime> // Includi <ctime> per struct timespec

class TimeStamp {
public:
    static const uint32_t TS_NOPPS = 0x01;
    static const uint32_t TS_NOUART = 0x02;
    static const uint32_t TS_OVFLOW = 0x04;

    TimeStamp();
    ~TimeStamp();

    int init();
    void destroy();

    struct CurrentTime {
        struct timespec ts;
        uint32_t hh;
        uint32_t mm;
        uint32_t ss;
        uint32_t us;
    };

    struct AbsoluteTime {
        uint32_t ppsSliceNo;
        uint32_t hh;
        uint32_t mm;
        uint32_t ss;
        uint32_t us;
        uint32_t year;
        uint32_t month;
        uint32_t day;
    };

    uint32_t read(CurrentTime *currTime);
    void computeAbsoluteTime(const struct timespec *ts, CurrentTime *currTime, AbsoluteTime *absTime);
};

#endif
