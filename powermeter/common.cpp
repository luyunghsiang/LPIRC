#include "common.h"

mytime::mytime(){
	begin_time = clock();
}

int mytime::elapsed_seconds(){
	clock_t now_time = clock();
	double elapsed_secs = double(now_time - begin_time) / CLOCKS_PER_SEC;
	return (int)elapsed_secs;
}