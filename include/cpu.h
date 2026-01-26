#ifndef CPU_H
#define CPU_H

struct cpu_capacity {
	int cores;
	long max_freq_khz;
};


struct cpu_stat {
	long user;
	long nice;
	long system;
	long idle;
};

int read_cpu_capacity(struct cpu_capacity *cap);
int read_cpu_stat(struct cpu_stat *out);
double cpu_usage(const struct cpu_stat *prev,
		const struct cpu_stat *curr);


#endif
