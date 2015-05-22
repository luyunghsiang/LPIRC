#ifndef __CONTROLLER__
#define __CONTROLLER__

#include <string>
#include <ctime>
#include <vector>
#include "settings.h"
#include "parameters.h"
#include "common.h"
using namespace std;


class pm_controller{
	clock_t begin_time;			//Constructor generated time
	char adr[100];
	int  id;
	string model_info;

	int set_itemx(e_wt_functions item_number, string pm_function);
	int set_display(int item_number, string pm_function);
	int set_mode(string pm_mode);
	int set_timeout(int pm_timeout);
	int get_model_info();
	int set_ipaddress(string pm_ipaddress);
	int set_data_update_rate(string pm_rate);
	int init_integrator(int pm_timer);
	int integrator(string pm_cmd);
	int yoko_send(string pm_cmd);
	int yoko_receive(string& pm_buf);
	double read_value(e_wt_functions item_number);
	int update_data_memory(pm_parameters& params_t);
	int update_element(pm_parameters& params_t, e_wt_functions item);

public:
	pm_controller();
	int init_ctl(pm_settings const& settings_t);
	int rst_ctl();
	int integrator_start();
	int integrator_stop();
	int integrator_reset();
	e_integrator_states integrator_state();
	int init_numeric_group();
	int poll_data(pm_settings const& settings_t, pm_parameters& params_t);
	int set_display_group();
};

#endif