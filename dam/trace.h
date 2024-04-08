#ifndef __TRACE_H__
#define __TRACE_H__

#include <cstdio>

/* Enable/disable trace macros */
//#define TRACEON         // Generic trace

#ifdef TRACEON
#define TRACE( format, ... )   printf( format, ##__VA_ARGS__ )
#else
#define TRACE( format, ... )
#endif

#endif // __TRACE_H__
