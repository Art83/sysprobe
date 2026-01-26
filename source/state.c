#include "state.h"
#include "mem.h"
#include <stdio.h>

const char *sys_state_str(sys_state s){
	switch (s) {
		case SYS_OK: return "ok";
		case SYS_WARN: return "warn";
		case SYS_DANGER: return "danger";
		default: return "unknown";
	}
};


sys_state cpu_state_from_avg(double avg){
	if(avg > 95.0) return SYS_DANGER;
	if(avg > 85.0) return SYS_WARN;
	return SYS_OK;
};


sys_state mem_state_from_capacity(const mem_stat *cap){
	if(!cap || cap->mem_total_kb == 0) return SYS_OK;

	double avail_ratio = 
		(double)cap->mem_avail_kb / cap->mem_total_kb;
	double swap_used = cap->swap_total_kb > 0 ?
		(double)(cap->swap_total_kb - cap->swap_free_kb)/cap->swap_total_kb
		: 0.0;
	if(avail_ratio < 0.05) return SYS_DANGER;
	if(avail_ratio < 0.1 || swap_used > 80) return SYS_WARN;

	return SYS_OK;
};
