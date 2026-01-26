#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>
#include "cpu.h"
#include "mem.h"
#include "sample.h"
#include "output.h"
#include "state.h"
#include "window.h"

volatile sig_atomic_t running = 1;

void handle_sigint(int sig){
	(void)sig;
	running = 0;
}

double now_sec(struct timespec *start){
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC,&t);
	return(t.tv_sec - start->tv_sec)
		+ (t.tv_nsec - start->tv_nsec)/1e9/1e9/1e9/1e9/1e9/1e9/1e9/1e9/1e9;
}



int main(int argc, char *argv[]){
	struct cpu_capacity cap;
	read_cpu_capacity(&cap);
	printf("CPU: %d cores", cap.cores);
	if(cap.max_freq_khz > 0){
		printf(", max freq %.2f GHz\n",
				cap.max_freq_khz / 1000000.0);
	}
	mem_stat mem;
	read_mem_stat(&mem);
	printf("MemTotal:%.2f Gb\nMemAvail:%.2f Gb\nSwapTotal:%.2f Gb\nSwapAvail:%.2f Gb\n",
			mem.mem_total_kb/1024.0/1024.0, 
			mem.mem_avail_kb/1024.0/1024.0, 
			mem.swap_total_kb/1024.0/1024.0, 
			mem.swap_free_kb/1024.0/1024.0);

	signal(SIGINT, handle_sigint);
	
	struct cpu_stat prev_cpu = {0};
	struct cpu_stat curr_cpu = {0};


	cpu_window cpu_win;
	cpu_window_init(&cpu_win);

	read_cpu_stat(&prev_cpu);

	struct timespec start;
	clock_gettime(CLOCK_MONOTONIC, &start);

	while (running) {
		sleep(1);

		if(read_cpu_stat(&curr_cpu) != 0) continue;

		double usage = cpu_usage(&prev_cpu, &curr_cpu);
		cpu_window_add(&cpu_win, usage);

		read_mem_stat(&mem);

		double avg_cpu = cpu_window_avg(&cpu_win);

		sys_state cpu_state = cpu_state_from_avg(avg_cpu);
        	sys_state mem_state = mem_state_from_capacity(&mem);
		float t = now_sec(&start);

		printf(
            		"{"
            		"\"ts\":%.0f,"
            		"\"cpu\":%.2f,"
            		"\"cpu_avg\":%.2f,"
			"\"mem_used\":%.2f,"
			"\"mem_avail\":%.2f,"
			"\"mem_swap_used\":%.2f,"
			"\"mem_swap_avail\":%.2f, "
            		"\"CPU_STATE\":\"%s\","
            		"\"MEM_STATE\":\"%s\""
            		"}\n",
            		t,
            		usage,
            		avg_cpu,
			(mem.mem_total_kb - mem.mem_avail_kb)/1024.0/1024.0,
			mem.mem_avail_kb/1024.0/1024.0,
			(mem.swap_total_kb - mem.swap_free_kb)/1024.0/1024.0,
			mem.swap_free_kb/1024.0,
            		sys_state_str(cpu_state),
            		sys_state_str(mem_state)
        		);

        	fflush(stdout);

        	prev_cpu = curr_cpu;
	}



	//struct timespec start;
	//clock_gettime(CLOCK_MONOTONIC, &start);

	//struct cpu_stat cpu_prev, cpu_curr;
	//struct mem_stat mem;

	//if(read_cpu_stat(&cpu_prev) != 0){
	//	perror("cpu");
	//	return 2;
	//}
	//sleep(1);

	/*while(running){
		struct sample s = {0};

		if (read_cpu_stat(&cpu_curr) == 0){
			s.cpu_pct = cpu_usage(&cpu_prev, &cpu_curr);
			cpu_prev = cpu_curr;
		}

		if (read_mem_stat(&mem) == 0){
			s.mem_used_gb = (mem.total_kb - mem.avail_kb) / 1024.0 / 1024.0;
		       	s.mem_avail_gb = mem.avail_kb / 1024.0 / 1024.0;
		}

		s.t = now_sec(&start);

		print_json(s.t, s.cpu_pct, s.mem_used_gb, s.mem_avail_gb);

		sleep(1);
	}*/
	
	return 0;
}



