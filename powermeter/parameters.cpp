#include <iostream>
#include <fstream>
#include "parameters.h"

eparam::eparam(){
	begin_time = clock();
	length = 0;
}

int eparam::push_data(vector<double> const& d_t){
	data.insert(data.end(), d_t.begin(), d_t.end());
	timestamp.push_back(clock());
	return 1;
}

int eparam::get_data_all(vector<double>& d_all){
	d_all = data;
	return 1;
}

int eparam::get_timestamp_all(vector<time_t>& ts_all){
	ts_all = timestamp;
	return 1;
}


pm_parameters::pm_parameters(){
	begin_time = clock();
}

int pm_parameters::write_csv(string filename){
	int ret;
	vector<time_t> ts_all;
	vector<double> v_all, i_all, p_all, e_all, it_all;

	voltage.get_timestamp_all(ts_all);
	voltage.get_data_all(v_all);
	current.get_data_all(i_all);
	power.get_data_all(p_all);
	energy.get_data_all(e_all);
	itime.get_data_all(it_all);
	
	/*Verify size match*/
	if ((ts_all.size() != v_all.size()) || (ts_all.size() != i_all.size()) || (ts_all.size() != p_all.size()) || \
		(ts_all.size() != e_all.size()) || (ts_all.size() != it_all.size())){
		cout << "Size mismatch" << endl;
		exit(EXIT_FAILURE);
	}

	/*Write to csv file*/
	ofstream myfile;
	myfile.open(&filename[0]);
	myfile << "Voltage (V), Current (A), Active Power (Watt), Accumulated Energy (Watt-Hour), Elapsed Time (Seconds)\n";
	for (int i = 0; i < v_all.size(); i++){
		myfile << v_all[i] << ",\t" << i_all[i] << ",\t" << \
			p_all[i] << ",\t" << e_all[i] << ",\t" << \
			it_all[i] << "\n";
	}
	myfile.close();

	return 1;
}

int pm_parameters::push_value(vector<double> const& v_t, e_wt_functions item){
	int status;

	switch (item)
	{
	case t_voltage:
		status = voltage.push_data(v_t);
		break;

	case t_current:
		status = current.push_data(v_t);
		break;

	case t_power:
		status = power.push_data(v_t);
		break;

	case t_energy:
		status = energy.push_data(v_t);
		break;

	case t_itime:
		status = itime.push_data(v_t);
		break;

	default:
		exit(EXIT_FAILURE);
	}

	return status;
}
