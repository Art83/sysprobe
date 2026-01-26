#ifndef WINDOW_H
#define WINDOW_H

#define CPU_WINDOW 10

typedef struct {
	double samples[CPU_WINDOW];
	int index;
	int count;
} cpu_window;


void cpu_window_init(cpu_window *w);
void cpu_window_add(cpu_window *w, double value);
double cpu_window_avg(const cpu_window *w);

#endif

