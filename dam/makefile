CFLAGS  = -g -Wall -Werror -std=c++11
CFLAGS += -I/opt/redpitaya/include
LDFLAGS = -L/opt/redpitaya/lib
LDLIBS = -lm -lpthread -lrp -lstdc++

all: main fifo globals datastore systeminfo configinfo tcp waveacq pugixml packet tchandler osc_fpga
	gcc -o dam *.o $(LDFLAGS) $(LDLIBS)

main: main.cpp
	gcc $(CFLAGS) -c main.cpp
	
fifo: fifo.cpp fifo.h
	gcc $(CFLAGS) -c fifo.cpp 

globals: globals.cpp globals.h
	gcc $(CFLAGS) -c globals.cpp 

datastore: datastore.cpp datastore.h
	gcc $(CFLAGS) -c datastore.cpp
	
systeminfo: systeminfo.cpp systeminfo.h
	gcc $(CFLAGS) -c systeminfo.cpp  

configinfo: configinfo.cpp configinfo.h
	gcc $(CFLAGS) -c configinfo.cpp  

tcp: tcp.cpp tcp.h
	gcc $(CFLAGS) -c tcp.cpp 

waveacq: waveacq.cpp waveacq.h
	gcc $(CFLAGS) -c waveacq.cpp 

pugixml: pugixml.cpp pugixml.hpp pugiconfig.hpp
	gcc $(CFLAGS) -c pugixml.cpp  

packet: packet.cpp packet.h
	gcc $(CFLAGS) -c packet.cpp  

tchandler: tchandler.cpp tchandler_acq.cpp tchandler_hk.cpp tchandler_test.cpp tchandler_wave.cpp tchandler.h
	gcc $(CFLAGS) -c tchandler.cpp
	gcc $(CFLAGS) -c tchandler_acq.cpp
	gcc $(CFLAGS) -c tchandler_hk.cpp
	gcc $(CFLAGS) -c tchandler_test.cpp
	gcc $(CFLAGS) -c tchandler_wave.cpp

osc_fpga: osc_fpga.cpp osc_fpga.h
	gcc $(CFLAGS) -c osc_fpga.cpp 
clean:
	rm *.o dam
