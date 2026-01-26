#include "window.h"

void cpu_window_init(cpu_window *w){
	w->index=0;
	w->count=0;
}

void cpu_window_add(cpu_window *w, double value){
	w->samples[w->index] = value;
	w->index = (w->index + 1) % CPU_WINDOW;
	if(w->count < CPU_WINDOW) w->count++;
}

double cpu_window_avg(const cpu_window *w){
	double sum=0.0;
	for(int i = 0; i < w->count; i++){
		sum+=w->samples[i];
	}
	return w->count ? sum / w->count: 0.0;
}

