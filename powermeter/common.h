#ifndef __COMMON_H__
#define __COMMON_H__

#include <ctime>

enum e_wt_functions{
	t_voltage = 1,
	t_current,
	t_power,
	t_energy,
	t_itime
};

enum e_integrator_states{
	invalid,
	i_start,
	i_stop,
	i_reset,
	i_timeout,
	i_error
};

class mytime{
	clock_t begin_time;			//Constructor generated time
public:
	mytime();
	int elapsed_seconds();
};

#endif