#include <stdio.h>

void print_json(
		double t,
		double cpu,
		double mem_used_gb,
		double mem_avail_gb
	       ) {
	printf(
        "{\"t\":%.1f,\"cpu\":%.1f,\"mem_used_gb\":%.2f,\"mem_avail_gb\":%.2f}\n",
        t, cpu, mem_used_gb, mem_avail_gb
    );
    fflush(stdout);
}
