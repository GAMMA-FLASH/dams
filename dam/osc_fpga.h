/**
 * $Id: osc_fpga.h 881 2013-12-16 05:37:34Z rp_jmenart $
 *
 * @brief Red Pitaya Oscilloscope FPGA Interface.
 *
 * @Author Jure Menart <juremenart@gmail.com>
 *         
 * (c) Red Pitaya  http://www.redpitaya.com
 *
 * This part of code is written in C programming language.
 * Please visit http://en.wikipedia.org/wiki/C_(programming_language)
 * for more details on the language used herein.
 */

#ifndef __OSC_FPGA_H__
#define __OSC_FPGA_H__

#include <stdint.h>
#include <unistd.h>

// Starting address of FPGA registers handling Oscilloscope module. 
#define OSC_FPGA_BASE_ADDR 	0x40100000UL 

// The size of FPGA registers handling Oscilloscope module. 
#define OSC_FPGA_BASE_SIZE 	0x30000 

// Size of data buffer into which input signal is captured , must be 2^n!.
#define OSC_FPGA_SIG_LEN   (16*1024)

// Offset to the memory buffer where signal on channel A is captured. 
#define OSC_FPGA_CHA_OFFSET	0x10000

// Offset to the memory buffer where signal on channel B is captured. 
#define OSC_FPGA_CHB_OFFSET	0x20000

// Trigger source register mask 
#define OSC_FPGA_TRIG_SRC_MASK 0x00000007

// Configuration register bit definitions
typedef enum {
	OSC_FPGA_CONF_TRIG_ARM 		= 1,
	OSC_FPGA_CONF_RESET 		= (1<<1),
	OSC_FPGA_CONF_TRIG_ARRIVED 	= (1<<2),
	OSC_FPGA_CONF_TRIG_KEEP  	= (1<<3),
	OSC_FPGA_CONF_DELAY_PASS 	= (1<<4),
} osc_fpga_conf_t;

// Equalizer
typedef enum {
	OSC_FPGA_EQ_OFF	= 0,
	OSC_FPGA_EQ_LV,
	OSC_FPGA_EQ_HV,
} osc_fpga_eq_t;

// Trigger source register possible values
typedef enum {
	OSC_FPGA_TSRC_TRIG_NOW = 1,
	OSC_FPGA_TSRC_CHA_POS  = 2,
	OSC_FPGA_TSRC_CHA_NEG  = 3,
	OSC_FPGA_TSRC_CHB_POS  = 4,
	OSC_FPGA_TSRC_CHB_NEG  = 5,
	OSC_FPGA_TSRC_EXT_POS  = 6,
	OSC_FPGA_TSRC_EXT_NEG  = 7,
	OSC_FPGA_TSRC_AWG_POS  = 8,
	OSC_FPGA_TSRC_AWG_NEG  = 9,
} osc_fpga_trig_source_t;

// Data decimation register possible values
typedef enum {
	OSC_FPGA_DEC1 		= 1,
	OSC_FPGA_DEC8 		= 8,
	OSC_FPGA_DEC64 		= 64,
	OSC_FPGA_DEC1024 	= 1024,
	OSC_FPGA_DEC8192 	= 8192,
	OSC_FPGA_DEC65536 	= 65536,
} osc_fpga_dec_t;

/* FPGA registry structure for Oscilloscope core module.
 * This structure is direct image of physical FPGA memory. It assures
 * direct read/write FPGA access when it is mapped to the appropriate memory address
 * through /dev/mem device.
 */
typedef struct {
    
    /* off  [0x00] Configuration:
     * bit  [31:5] - Reserved
     * bit     [4] - ACQ delay has passed / (all data was written to buffer)
     * bit     [3] - Trigger remains armed after ACQ delay passes
     * bit     [2] - Trigger has arrived stays on (1) until next arm or reset
     * bit     [1] - Reset write state machine
     * bit     [0] - Arm trigger
     */
    uint32_t conf;

    /* off  [0x04] Trigger source:
     * bits [31:4] - Reserved
     * bits  [3:0] - Trigger source:
     *   1 - trig immediately
     *   2 - ChA positive edge
     *   3 - ChA negative edge
     *   4 - ChB positive edge 
     *   5 - ChB negative edge
     *   6 - External trigger positive edge (DIO0_P)
     *   7 - External trigger negative edge 
     *   8 - AWG positive edge
     *   9 - AWG negative edge 
     */
    uint32_t trig_source;

    /* off   [0x08] ChA threshold:
     * bits [31:14] - Reserved
     * bits  [13:0] - ChA threshold
     */
    uint32_t cha_thr;

    /* off   [0x0C] ChB threshold:
     * bits [31:14] - Reserved
     * bits  [13:0] - ChB threshold
     */
    uint32_t chb_thr;

    /* off  [0x10] After trigger delay:
     * bits [31:0] - Trigger delay, how many decimated samples should be stored into a buffer (max 16k samples) 
     */
    uint32_t trigger_delay;

    /* off   [0x14] Data decimation
     * bits [31:16] - Reserved
     * bits  [15:0] - Decimation factor, legal values: 1, 8, 64, 1024, 8192 65536
     * If other values are written data is undefined 
     */
    uint32_t data_dec;

    /* off   [0x18] Current write pointer:
     * bits [31:14] - Reserved
     * bits  [13:0] - Current pointer i.e. where machine stopped writing after trigger 
     */
    uint32_t wr_ptr_curr;
    
    /* off   [0x1C] Trigger write pointer:
     * bits [31:14] - Reserved
     * bits  [13:0] - Trigger pointer i.e. where where trigger was detected 
     */
    uint32_t wr_ptr_trig;

    /* off   [0x20] ChA hysteresis:
     * bits [31:14] - Reserved
     * bits  [13:0] - Hysteresis threshold
     */
    uint32_t cha_hyst;
    
    /* off   [0x24] ChB hysteresis:
     * bits [31:14] - Reserved
     * bits  [13:0] - Hysteresis threshold
     */
    uint32_t chb_hyst;

    /* off [0x28] Signal average at decimation
     * bits [31:1] - Reserved
     * bit     [0] - Enable signal average at decimation
     */
    uint32_t averaging;
    
    /* off  [0x2C] Pre Trigger counter
     * bits [31:0] - how many decimated samples have been stored into a buffer
     * before trigger arrived. The value does not overflow, instead it stops 
     * incrementing at 0xffffffff.
     */
    uint32_t pre_trig_count;
    
    /* off   [0x30] ChA Equalization filter
     * bits [31:18] - Reserved
     * bits  [17:0] - AA coefficient (pole)
     */
    uint32_t cha_filt_aa;    
    
    /* off   [0x34] ChA Equalization filter
     * bits [31:18] - Reserved
     * bits  [17:0] - BB coefficient
     */
    uint32_t cha_filt_bb;    
    
    /* off   [0x38] ChA Equalization filter
     * bits [31:18] - Reserved
     * bits  [17:0] - KK coefficient
     */
    uint32_t cha_filt_kk;  
    
    /* off   [0x3C] ChA Equalization filter
     * bits [31:18] - Reserved
     * bits  [17:0] - PP coefficient
     */
    uint32_t cha_filt_pp;     
    
    /* off   [0x40] ChB Equalization filter
     * bits [31:18] - Reserved
     * bits  [17:0] - AA coefficient (pole)
     */
    uint32_t chb_filt_aa;    
    
    /* off   [0x44] ChB Equalization filter
     * bits [31:18] - Reserved
     * bits  [17:0] - BB coefficient
     */
    uint32_t chb_filt_bb;    
    
    /* off   [0x48] ChB Equalization filter
     * bits [31:18] - Reserved
     * bits  [17:0] - KK coefficient
     */
    uint32_t chb_filt_kk;  
    
    /* off   [0x4C] ChB Equalization filter
     * bits [31:18] - Reserved
     * bits  [17:0] - PP coefficient
     */
    uint32_t chb_filt_pp;
    
    /* off   [0x50] ChA AXI lower address
     * bits  [31:0] - Starting writing address
     */
    uint32_t cha_axi_lower_addr;
    
    /* off   [0x54] ChA AXI upper address
     * bits  [31:0] - Address where it jumps to lower
     */
    uint32_t cha_axi_upper_addr;
    
    /* off   [0x58] ChA AXI delay after trigger
     * bits  [31:0] - Number of decimated data after trigger written into memory
     */
    uint32_t cha_axi_after_trig;
    
    /* off   [0x5C] ChA AXI enable master
     * bits  [31:1] - Reserved
     * bit      [0] - Enable AXI master
     */
    uint32_t cha_axi_enable_master;
    
    /* off   [0x60] ChA AXI trigger write pointer
     * bits  [31:0] - Write pointer at time when trigger arrived
     */
    uint32_t cha_axi_wr_ptr_trig;
    
    /* off   [0x64] ChA AXI current write pointer
     * bits  [31:0] - Current write pointer
     */
    uint32_t cha_axi_wr_ptr_curr;
    
    // Dummy vars to shift ChB AXI reg. to 0x70
    // off [0x68]
	uint32_t dummy0;
	// off [0x6C]
	uint32_t dummy1;
    
    /* off   [0x70] ChB AXI lower address
     * bits  [31:0] - Starting writing address
     */
    uint32_t chb_axi_lower_addr;
    
    /* off   [0x74] ChB AXI upper address
     * bits  [31:0] - Address where it jumps to lower
     */
    uint32_t chb_axi_upper_addr;
    
    /* off   [0x78] ChB AXI delay after trigger
     * bits  [31:0] - Number of decimated data after trigger written into memory
     */
    uint32_t chb_axi_after_trig;
    
    /* off   [0x7C] ChB AXI enable master
     * bits  [31:1] - Reserved
     * bit      [0] - Enable AXI master
     */
    uint32_t chb_axi_enable_master;
    
    /* off   [0x80] ChB AXI trigger write pointer
     * bits  [31:0] - Write pointer at time when trigger arrived
     */
    uint32_t chb_axi_wr_ptr_trig;
    
    /* off   [0x84] ChB AXI current write pointer
     * bits  [31:0] - Current write pointer
     */
     uint32_t chb_axi_wr_ptr_curr;   
     
    // Dummy vars to shift debouncer reg. to 0x90
    // off [0x88]
	uint32_t dummy2;
	// off [0x8C]
	uint32_t dummy3;
     
    /* off   [0x90] Trigger debouncer time
     * bits  [31:0] - Number of ADC clock periods trigger is disabled after activation reset value is decimal 62500 or equivalent to 0.5ms
     */
    uint32_t trig_debounce;  
    
    // off   [0xA0] Accumulator data sequence length
    // off   [0xA4] Accumulator data offset correction ChA
    // off   [0xA0] Accumulator data offset correction ChB
    
    /* @brief  ChA & ChB data - 14 LSB bits valid starts from 0x10000 and
     * 0x20000 and are each 16k samples long */
     
} osc_fpga_reg_mem_t;

/** @} */
extern osc_fpga_reg_mem_t	*g_osc_fpga_reg_mem;
extern uint32_t           	*g_osc_fpga_cha_mem;
extern uint32_t           	*g_osc_fpga_chb_mem;
extern int                 	g_osc_fpga_mem_fd;
extern const int   			g_osc_fpga_adc_bits;
extern const float 			g_osc_fpga_smpl_freq;
extern const float 			g_osc_fpga_smpl_period;

/* function declarations, detailed descriptions is in apparent implementation file  */
int osc_fpga_init(void);
int osc_fpga_uninit(void);

int osc_fpga_reset();
int osc_fpga_cha_set_filter(int equalizer, int shaping);
int osc_fpga_chb_set_filter(int equalizer, int shaping);

int osc_fpga_set_decimation(int decimation);
int osc_fpga_set_averaging(int averaging);

int osc_fpga_cha_set_trigger_par(int thresh, int hyst);
int osc_fpga_chb_set_trigger_par(int thresh, int hyst);

int osc_fpga_set_trigger_delay(int delay);
int osc_fpga_set_trigger_debounce(int debounce);

int osc_fpga_set_trigger_source(int trig_source);
int osc_fpga_arm_trigger();
int osc_fpga_wait_trigger(useconds_t usec);

#endif // __OSC_FPGA_H__