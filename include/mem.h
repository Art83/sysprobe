#ifndef MEM_H
#define MEM_H

typedef struct {
	long mem_total_kb;
	long mem_avail_kb;
	long swap_total_kb;
	long swap_free_kb;
} mem_stat;

int read_mem_stat(mem_stat *out);

#endif
