CFLAGS  = -g -Wall -Werror -std=c++11
CFLAGS += -Wno-unused-function -Wno-unused-variable -I/opt/redpitaya/include
LDFLAGS = -L/opt/redpitaya/lib
LDLIBS = -lm -lpthread -lrp -lstdc++

all: main hk_fpga uart tstamp
	gcc -o gpstime *.o $(LDFLAGS) $(LDLIBS)

main: main.cpp
	gcc $(CFLAGS) -c main.cpp

hk_fpga: hk_fpga.cpp hk_fpga.h
	gcc $(CFLAGS) -c hk_fpga.cpp
	
uart: uart.cpp uart.h
	gcc $(CFLAGS) -c uart.cpp 
	
tstamp: tstamp.cpp tstamp.h
	gcc $(CFLAGS) -c tstamp.cpp  

clean:
	rm *.o gpstime
