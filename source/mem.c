#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include "mem.h"


int read_mem_stat(mem_stat *cap){
	if(!cap) return -1;
	cap->mem_total_kb = 0;
	cap->mem_avail_kb = 0;
	cap->swap_total_kb = 0;
	cap->swap_free_kb = 0;
	FILE *f = fopen("/proc/meminfo", "r");
	if(!f){
		perror("fopen /proc/meminfo");
		return -1;
	}
	char key[32];
	long value;
	char unit[16];
	
	int cnt = 0;
	while(fscanf(f, "%31s %ld %15s", key, &value, unit) == 3){
		if(strcmp(key, "MemTotal:") == 0){
			cap->mem_total_kb = value;cnt++;
		} else if (strcmp(key, "MemAvailable:") == 0){
			cap->mem_avail_kb = value;cnt++;
		} else if (strcmp(key, "SwapTotal:") == 0){
			cap->swap_total_kb = value;cnt++;
		} else if (strcmp(key, "SwapFree:") == 0){
			cap->swap_free_kb = value;cnt++;
		}
		if(cnt==4) break;

	}
	fclose(f);
	return 0;
}


