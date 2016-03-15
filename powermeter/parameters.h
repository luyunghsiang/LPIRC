#ifndef __PARAMETERS__
#define __PARAMETERS__

#include <string>
#include <ctime>
#include <vector>
#include "common.h"
using namespace std;

class eparam{
	clock_t begin_time;			//Constructor generated time
	vector<double> data;
	vector<time_t> timestamp;
	int length;
public:
	eparam();
	int push_data(vector<double> const& d_t);
	int get_data_all(vector<double>& d_all);
	int get_timestamp_all(vector<time_t>& ts_all);
};


class pm_parameters
{
	clock_t begin_time;			//Constructor generated time
	eparam voltage;
	eparam current;
	eparam power;
	eparam energy;
	eparam itime;
public:
	pm_parameters();
	double elapsed_time();
	int push_value(vector<double> const& v_t, e_wt_functions item);
	int write_csv(string filename);
	int write_csv_cont(string filename);
};



#endif