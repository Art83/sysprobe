#include <stdio.h>
#include <unistd.h>
#include "cpu.h"



int read_cpu_capacity(struct cpu_capacity *cap){
	if(!cap) return -1;
	long cores = sysconf(_SC_NPROCESSORS_ONLN);
       	if(cores < 1) cores = 1;
	cap->cores = (int)cores;
	cap->max_freq_khz = -1;	
	FILE *f = fopen("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq", "r");
	if (!f) {
		printf("Frequency info is not exposed.");
	} else {
		fscanf(f,"%ld",&cap->max_freq_khz);
	}

	fclose(f);
	return 0;
}

double cpu_usage(const struct cpu_stat *prev,
		const struct cpu_stat *curr){
	long prev_idle = prev->idle;
	long curr_idle = curr->idle;

	long prev_total = prev->user +
		prev->nice + 
		prev->system +
		prev->idle;
	long curr_total = curr->user +
		curr->nice +
		curr->system+
		curr->idle;
	long total_delta = curr_total - prev_total;
	long idle_delta = curr_idle - prev_idle;

	if(total_delta == 0) return 0.0;

	return 100.0 * (total_delta - idle_delta) / total_delta;
	
}


int read_cpu_stat(struct cpu_stat *out) {
    FILE *f = fopen("/proc/stat", "r");
    if (!f)
        return -1;

    int n = fscanf(f, "cpu %ld %ld %ld %ld",
                    &out->user,
                    &out->nice,
                    &out->system,
                    &out->idle);

    fclose(f);
    return (n == 4) ? 0 : -1;
}
