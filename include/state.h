#ifndef STATE_H
#define STATE_H
#include "mem.h"

typedef enum {
	SYS_OK = 0,
	SYS_WARN,
	SYS_DANGER
} sys_state;

const char *sys_state_str(sys_state s);

sys_state cpu_state_from_avg(double avg);       
sys_state mem_state_from_capacity(const mem_stat *cap);


#endif
