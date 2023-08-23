/**
 * $Id: fpga_osc.c 881 2013-12-16 05:37:34Z rp_jmenart $
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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <errno.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include "osc_fpga.h"

/* @brief Pointer to FPGA control registers. */
osc_fpga_reg_mem_t *g_osc_fpga_reg_mem = NULL;

/* @brief Pointer to data buffer where signal on channel A is captured.  */
uint32_t           *g_osc_fpga_cha_mem = NULL;

/* @brief Pointer to data buffer where signal on channel B is captured.  */
uint32_t           *g_osc_fpga_chb_mem = NULL;

/* @brief The memory file descriptor used to mmap() the FPGA space. */
int                 g_osc_fpga_mem_fd = -1;

/* @brief Number of ADC acquisition bits.  */
const int 			g_osc_fpga_adc_bits = 14;

/* @brief Sampling frequency = 125Mspmpls (non-decimated). */
const float         g_osc_fpga_smpl_freq = 125e6;

/* @brief Sampling period (non-decimated) - 8 [ns]. */
const float         g_osc_fpga_smpl_period = (1./125e6);

/*--------------------------------------------------------------------------------------*
 * Init FPGA memory buffers
 *
 * Open memory device and performs memory mapping
 * has already been established it unmaps logical memory regions and close apparent
 * file descriptor.
 *
 * @retval  0 Success
 * @retval -1 Failure, error message is printed on standard error device
 *--------------------------------------------------------------------------------------*/
int osc_fpga_init(void) {

    void *page_ptr;
    long page_addr, page_off, page_size;
    
    page_size = sysconf(_SC_PAGESIZE);

    /* If maybe needed, cleanup the FD & memory pointer */
    if(osc_fpga_uninit() < 0) {
    	return -1;
    }
        
    g_osc_fpga_mem_fd = open("/dev/mem", O_RDWR | O_SYNC);
    if(g_osc_fpga_mem_fd < 0) {
        fprintf(stderr, "open(/dev/mem) failed: %s\n", strerror(errno));
        return -1;
    }

    page_addr = OSC_FPGA_BASE_ADDR & (~(page_size-1));
    page_off  = OSC_FPGA_BASE_ADDR - page_addr;

    page_ptr = mmap(NULL, OSC_FPGA_BASE_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, g_osc_fpga_mem_fd, page_addr);
    if((void *)page_ptr == MAP_FAILED) {
        fprintf(stderr, "mmap() failed: %s\n", strerror(errno));
        osc_fpga_uninit();
        return -1;
    }
    g_osc_fpga_reg_mem = (osc_fpga_reg_mem_t*)((uint8_t*)page_ptr + page_off);
    g_osc_fpga_cha_mem = (uint32_t*)((uint8_t*)g_osc_fpga_reg_mem + OSC_FPGA_CHA_OFFSET);
    g_osc_fpga_chb_mem = (uint32_t*)((uint8_t*)g_osc_fpga_reg_mem + OSC_FPGA_CHB_OFFSET);

    return 0;
    
}

/*--------------------------------------------------------------------------------------*
 * Cleanup access to FPGA memory buffers
 *
 * Function optionally cleanups access to FPGA memory buffers, i.e. if access
 * has already been established it unmaps logical memory regions and close apparent
 * file descriptor.
 *
 * @retval  0 Success
 * @retval -1 Failure, error message is printed on standard error device
 *--------------------------------------------------------------------------------------*/
int osc_fpga_uninit(void) {

    /* optionally unmap memory regions  */
    if (g_osc_fpga_reg_mem) {
        if (munmap(g_osc_fpga_reg_mem, OSC_FPGA_BASE_SIZE) < 0) {
            fprintf(stderr, "munmap() failed: %s\n", strerror(errno));
            return -1;
        }
        /* Update memory pointers */
        g_osc_fpga_reg_mem = NULL;
        g_osc_fpga_cha_mem = NULL;
        g_osc_fpga_chb_mem = NULL;
    }

    /* optionally close file descriptor */
    if(g_osc_fpga_mem_fd >= 0) {
        close(g_osc_fpga_mem_fd);
        g_osc_fpga_mem_fd = -1;
    }

    return 0;
    
}

int osc_fpga_reset() {

	if (g_osc_fpga_reg_mem == NULL) {
		return -1;
	}
	
	g_osc_fpga_reg_mem->conf = OSC_FPGA_CONF_RESET;
	
	return 0;
	
}

int osc_fpga_cha_set_filter(int equalizer, int shaping) {

	if (g_osc_fpga_reg_mem == NULL) {
		return -1;
	}
	
	switch (equalizer) {
	case OSC_FPGA_EQ_HV:
		g_osc_fpga_reg_mem->cha_filt_aa = 0x4c5f;   /* filter coeff aa */
		g_osc_fpga_reg_mem->cha_filt_bb = 0x2f38b;  /* filter coeff bb */
		break;
	case OSC_FPGA_EQ_LV:
		g_osc_fpga_reg_mem->cha_filt_aa = 0x7d93;   /* filter coeff aa */
		g_osc_fpga_reg_mem->cha_filt_bb = 0x437c7;  /* filter coeff bb */
		break;
	case OSC_FPGA_EQ_OFF:
		g_osc_fpga_reg_mem->cha_filt_aa = 0x0;      /* filter coeff aa */
		g_osc_fpga_reg_mem->cha_filt_bb = 0x0;      /* filter coeff bb */
		break;
	default:
		return -1;
	}

	/* shaping filter */
	if (shaping) {
		g_osc_fpga_reg_mem->cha_filt_kk = 0xd9999a; /* filter coeff kk */
		g_osc_fpga_reg_mem->cha_filt_pp = 0x2666;   /* filter coeff pp */
	} else {
		g_osc_fpga_reg_mem->cha_filt_kk = 0xffffff; /* filter coeff kk */
		g_osc_fpga_reg_mem->cha_filt_pp = 0x0;      /* filter coeff pp */
	}
	
	return 0;
	
}

int osc_fpga_chb_set_filter(int equalizer, int shaping) {

	if (g_osc_fpga_reg_mem == NULL) {
		return -1;
	}
	
	switch (equalizer) {
	case OSC_FPGA_EQ_HV:
		g_osc_fpga_reg_mem->chb_filt_aa = 0x4c5f;   /* filter coeff aa */
		g_osc_fpga_reg_mem->chb_filt_bb = 0x2f38b;  /* filter coeff bb */
		break;
	case OSC_FPGA_EQ_LV:
		g_osc_fpga_reg_mem->chb_filt_aa = 0x7d93;   /* filter coeff aa */
		g_osc_fpga_reg_mem->chb_filt_bb = 0x437c7;  /* filter coeff bb */
		break;
	case OSC_FPGA_EQ_OFF:
		g_osc_fpga_reg_mem->chb_filt_aa = 0x0;      /* filter coeff aa */
		g_osc_fpga_reg_mem->chb_filt_bb = 0x0;      /* filter coeff bb */
		break;
	default:
		return -1;
	}

	/* shaping filter */
	if (shaping) {
		g_osc_fpga_reg_mem->chb_filt_kk = 0xd9999a; /* filter coeff kk */
		g_osc_fpga_reg_mem->chb_filt_pp = 0x2666;   /* filter coeff pp */
	} else {
		g_osc_fpga_reg_mem->chb_filt_kk = 0xffffff; /* filter coeff kk */
		g_osc_fpga_reg_mem->chb_filt_pp = 0x0;      /* filter coeff pp */
	}
	
	return 0;
	
}

int osc_fpga_set_decimation(int decimation) {
	
	if (g_osc_fpga_reg_mem == NULL) {
		return -1;
	}
	
	g_osc_fpga_reg_mem->data_dec = decimation;
	
	return 0;

}

int osc_fpga_set_averaging(int averaging) {

	if (g_osc_fpga_reg_mem == NULL) {
		return -1;
	}
	
	g_osc_fpga_reg_mem->averaging = (averaging == 0) ? 0 : 1;
	
	return 0;

}

int osc_fpga_cha_set_trigger_par(int thresh, int hyst) {

	if (g_osc_fpga_reg_mem == NULL) {
		return -1;
	}
	
	g_osc_fpga_reg_mem->cha_thr = thresh;
	g_osc_fpga_reg_mem->cha_hyst = hyst;
	
	return 0;

}

int osc_fpga_chb_set_trigger_par(int thresh, int hyst) {

	if (g_osc_fpga_reg_mem == NULL) {
		return -1;
	}
	
	g_osc_fpga_reg_mem->chb_thr = thresh;
	g_osc_fpga_reg_mem->chb_hyst = hyst;
	
	return 0;

}

int osc_fpga_set_trigger_delay(int delay) {

	if (g_osc_fpga_reg_mem == NULL) {
		return -1;
	}
	
	g_osc_fpga_reg_mem->trigger_delay = delay;
	
	return 0;
	
}

int osc_fpga_set_trigger_debounce(int debounce) {

	if (g_osc_fpga_reg_mem == NULL) {
		return -1;
	}
	
	g_osc_fpga_reg_mem->trig_debounce = debounce;
	
	return 0;

}

int osc_fpga_set_trigger_source(int trig_source) {

	if (g_osc_fpga_reg_mem == NULL) {
		return -1;
	}
	
	g_osc_fpga_reg_mem->trig_source = trig_source;
	
	return 0;

}

int osc_fpga_arm_trigger() {

	if (g_osc_fpga_reg_mem == NULL) {
		return -1;
	}
	
	g_osc_fpga_reg_mem->conf |= OSC_FPGA_CONF_TRIG_ARM;
	
	return 0;

}

int osc_fpga_wait_trigger(useconds_t usec) {
	
	if (g_osc_fpga_reg_mem == NULL) {
		return -1;
	}
	
	// The trigger source register is set before arming the trigger and it is cleared
	// by the FPGA when the acquisition ended.
	// After the end of the acquisition the current write position is constant.
	
	//while (g_osc_fpga_reg_mem->trig_source) {
	//	usleep(usec);
	//}
	
	//return 0;
	//printf("--------------------------------------\n");
	for (int i = 0; i < 10000; i++) {
		//printf("%08X %08X\n", g_osc_fpga_reg_mem->trig_source, g_osc_fpga_reg_mem->conf);
		if (g_osc_fpga_reg_mem->conf & OSC_FPGA_CONF_DELAY_PASS) {
			return 0;
		} else {
//printf("%08X %08X\n", g_osc_fpga_reg_mem->trig_source, g_osc_fpga_reg_mem->conf);
			usleep(usec);
		}
	}
			
	return -1;
}
