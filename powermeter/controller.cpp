#include <iostream>
#include <fstream>
#include <chrono>
#include <thread>
#include "controller.h"
#include <Windows.h>
#include "tmctl.h"

/*Constants*/
const int MY_1SEC = 1000; //milliseconds
const string T100MS("100MS");
const string T250MS("250MS");
const string T500MS("500MS");
const string T1S("1S");

/*Integrator States*/
const string INT_STATE_START("STAR");
const string INT_STATE_STOP("STOP");
const string INT_STATE_RESET("RES");
const string INT_STATE_TIMEOUT("TIM");
const string INT_STATE_ERROR("ERR");

/* Yokogawa Controller Commands*/
/* Modes*/
const string YCMD_MODE_DC(":INPUT:MODE DC");
const string YCMD_MODE_RMS(":INPUT:MODE RMS");
/*Reset*/
const string YCMD_RST("*RST");
/*Model information*/
const string YCMD_IDN("*IDN?");
/*Numeric Item<x>*/
const string YCMD_ITEMX(":NUMERIC:NORMAL:ITEM"); 
/*Display group*/
const string YCMD_DISPLAY(":DISPLAY:NORMAL:ITEM");
/*WT310 Functions*/
const string YCMD_FORMAT_FLOAT(":NUMERIC:FORMAT FLOAT");
const string YCMD_FORMAT_ASCII(":NUMERIC:FORMAT ASCII");
const string YCMD_GET_ITEM_COUNT(":NUMERIC:NORMAL:NUMBER?");
const string YCMD_GET_VALUE(":NUMERIC:NORMAL:VALUE?"); //cmd [1-255]
const string YCMD_FUN_VOLTAGE("U");
const string YCMD_FUN_CURRENT("I");
const string YCMD_FUN_POWER("P");
const string YCMD_FUN_ENERGY("WH");
const string YCMD_FUN_ITIME("TIME");
/*Data update interval*/
const string YCMD_RATE(":RATE");
/*Integrator commands*/
const string YCMD_INT_MODE_NORMAL(":INTEGRATE:MODE NORMAL");
const string YCMD_INT_TIMER(":INTEG:TIM"); //Ex: cmd hour,min,sec
const string YCMD_INT_X(":INTEGRATE:");
const string YCMD_INT_STATE("STATE?");

pm_controller::pm_controller(){
	begin_time = clock();
}

int pm_controller::init_ctl(pm_settings const& settings_t){

	/* Set ip address*/
	set_ipaddress(settings_t.ipaddress);
	if (settings_t.ping){
		exit(EXIT_SUCCESS);
	}
	if (settings_t.stop == 1){
		integrator_stop();
		exit(EXIT_SUCCESS);
	}

	/* Hard Reset power meter*/
	if (settings_t.hard_reset){
		rst_ctl();
	}

	/* Get power meter model information*/
	get_model_info();

	/* Set timeout*/
	set_timeout(300);

	/* Set mode*/
	set_mode(settings_t.mode);

	/*Init numeric group*/
	init_numeric_group();
	
	/*Set data update rate*/
	set_data_update_rate(T1S);

	/*Init integrator*/
	init_integrator(settings_t.log_duration);

	/*Set Powermeter display*/
	set_display_group();

	return 1;
}

double pm_controller::read_value(e_wt_functions item_number){
	int ret;
	string yoko_cmd, yoko_buf;
	float ieee_float = 0.0;
	char *ieee_4byte;
	int buf_len;
	
	ieee_4byte = (char *)&ieee_float;

	yoko_cmd.assign(YCMD_GET_VALUE);
	yoko_cmd.push_back('\t');
	yoko_cmd.append(to_string(item_number));
	ret = yoko_send(yoko_cmd);
	ret = yoko_receive(yoko_buf);

	/*Get 4 byte IEEE Float*/
	buf_len = yoko_buf.length();
	yoko_buf.copy(&ieee_4byte[0], 1, buf_len - 2);
	yoko_buf.copy(&ieee_4byte[1], 1, buf_len - 3);
	yoko_buf.copy(&ieee_4byte[2], 1, buf_len - 4);
	yoko_buf.copy(&ieee_4byte[3], 1, buf_len - 5);


	return (double)ieee_float;
}

int pm_controller::set_display_group(){
	int ret;
	string yoko_cmd;

	/*Set display group A-D*/
	set_display(1, YCMD_FUN_ITIME);
	set_display(2, YCMD_FUN_VOLTAGE);
	set_display(3, YCMD_FUN_ENERGY);
	set_display(4, YCMD_FUN_CURRENT);

	return 1;
}

int pm_controller::init_numeric_group(){
	int ret;
	string yoko_cmd;

	/*Set Numeric format Float*/
	yoko_cmd.assign(YCMD_FORMAT_FLOAT);
	ret = yoko_send(yoko_cmd);

	/* Set item 1-x*/
	set_itemx(t_voltage, YCMD_FUN_VOLTAGE);
	set_itemx(t_current, YCMD_FUN_CURRENT);
	set_itemx(t_power, YCMD_FUN_POWER);
	set_itemx(t_energy, YCMD_FUN_ENERGY);
	set_itemx(t_itime, YCMD_FUN_ITIME);

	return 1;
}

int pm_controller::yoko_send(string pm_cmd){
	int ret;
	string yoko_cmd(pm_cmd);

	ret = TmcSend(id, &yoko_cmd[0u]);
	if (ret != 0) {
		cout << "Error sending cmd" << endl;
		exit(EXIT_FAILURE);
	}
	/*Wait for x seconds*/
	//std::this_thread::sleep_for(std::chrono::milliseconds(100));
	return 1;
}

int pm_controller::yoko_receive(string& pm_buf){
	int ret;
	char buf[1000];
	int  length;

	ret = TmcReceive(id, buf, 1000, &length);
	if (ret != 0) {
		cout << "Error receiving" << endl;
		exit(EXIT_FAILURE);
	}
	pm_buf.assign(buf, length);

	return 1;
}

int pm_controller::integrator(string pm_cmd){
	int ret;
	string yoko_cmd(YCMD_INT_X);

	yoko_cmd.append(pm_cmd);

	ret = yoko_send(yoko_cmd);
	/*ret = TmcSend(id, &yoko_cmd[0u]);
	if (ret != 0) {
		cout << "Error integrator task" << endl;
		exit(EXIT_FAILURE);
	}*/

	/*Verify integrator state*/
	string yoko_buf;
	yoko_cmd.assign(YCMD_INT_X);
	yoko_cmd.append(YCMD_INT_STATE);
	ret = yoko_send(yoko_cmd);
	ret = yoko_receive(yoko_buf);
	while (pm_cmd.compare(0, 3, yoko_buf, 0, 3)){
		std::this_thread::sleep_for(std::chrono::seconds(1));
		ret = yoko_send(yoko_cmd);
		ret = yoko_receive(yoko_buf);
	}

	return 1;
}

e_integrator_states pm_controller::integrator_state(){
	int ret;
	string yoko_buf, yoko_cmd;
	yoko_cmd.assign(YCMD_INT_X);
	yoko_cmd.append(YCMD_INT_STATE);
	ret = yoko_send(yoko_cmd);
	ret = yoko_receive(yoko_buf);
	yoko_buf.pop_back();

	if (yoko_buf.compare(INT_STATE_START) == 0){
		return i_start;
	}
	else if (yoko_buf.compare(INT_STATE_STOP) == 0){
		return i_stop;
	}
	else if (yoko_buf.compare(INT_STATE_RESET) == 0){
		return i_reset;
	}
	else if (yoko_buf.compare(INT_STATE_TIMEOUT) == 0){
		return i_timeout;
	}
	else if (yoko_buf.compare(INT_STATE_ERROR) == 0){
		return i_error;
	}
	else{
		return invalid;
	}
}

int pm_controller::integrator_start(){
	string task(INT_STATE_START);
	return integrator(task);
}

int pm_controller::integrator_stop(){
	e_integrator_states int_state;

	int_state = integrator_state();
	if (int_state == i_start){
		return integrator(INT_STATE_STOP);
	}
	else{
		// Do Nothing
		return 1;
	}
}

int pm_controller::integrator_reset(){
	e_integrator_states int_state;

	int_state = integrator_state();
	switch (int_state){
	case i_start:
		integrator_stop();
		return integrator(INT_STATE_RESET);
	default:
		return integrator(INT_STATE_RESET);
	}
}


int pm_controller::init_integrator(int pm_timer){
	int ret;
	string yoko_cmd;

	integrator_reset();
	/*Set normal integrator mode*/
	yoko_cmd.assign(YCMD_INT_MODE_NORMAL);
	ret = yoko_send(yoko_cmd);
	/*ret = TmcSend(id, &yoko_cmd[0u]);
	if (ret != 0) {
		cout << "Error setting integrator mode" << endl;
		exit(EXIT_FAILURE);
	}*/

	/*Set timer*/
	int t_hour = (int)(pm_timer / 3600);
	int t_rem = pm_timer - (int)(t_hour * 3600);
	int t_min = (int)(t_rem / 60);
	int t_sec = (t_rem % 60);
	yoko_cmd.assign(YCMD_INT_TIMER);
	yoko_cmd.push_back('\t');
	yoko_cmd.append(to_string(t_hour));
	yoko_cmd.push_back(',');
	yoko_cmd.append(to_string(t_min));
	yoko_cmd.push_back(',');
	yoko_cmd.append(to_string(t_sec));

	ret = yoko_send(yoko_cmd);
	/*ret = TmcSend(id, &yoko_cmd[0u]);
	if (ret != 0) {
		cout << "Error setting integrator timer" << endl;
		exit(EXIT_FAILURE);
	}*/

	/*Verify if integrator set*/
	string yoko_exp(yoko_cmd);
	string yoko_buf;
	int cmd_len;
	yoko_exp.push_back('\n');
	yoko_cmd.assign(YCMD_INT_TIMER);
	yoko_cmd.push_back('?');
	ret = yoko_send(yoko_cmd);

	cmd_len = yoko_cmd.size();
	ret = yoko_receive(yoko_buf);
	while (yoko_exp.compare(cmd_len, yoko_exp.size(), yoko_buf, cmd_len, yoko_buf.size())){
		std::this_thread::sleep_for(std::chrono::seconds(1));
		ret = yoko_send(yoko_cmd);
		ret = yoko_receive(yoko_buf);
	}


	return 1;
}

int pm_controller::set_data_update_rate(string pm_rate){
	int ret;
	string yoko_cmd;
	yoko_cmd.assign(YCMD_RATE);
	yoko_cmd.push_back('\t');
	yoko_cmd.append(pm_rate);

	ret = yoko_send(yoko_cmd);
	/*ret = TmcSend(id, &yoko_cmd[0u]);
	if (ret != 0) {
		cout << "Error setting rate" << endl;
		exit(EXIT_FAILURE);
	}*/

	return 1;
}

int pm_controller::set_ipaddress(string pm_ipaddress){
	int ret;
	string ipaddress(pm_ipaddress);

	ret = TmcInitialize(TM_CTL_VXI11, &ipaddress[0u], &id); //VXI-11 protocol
	if (ret != 0){
		cout << "IP Address not found" << endl;
		exit(EXIT_FAILURE);
	}

	return 1;
}

int pm_controller::get_model_info(){
	int ret;
	string yoko_cmd(YCMD_IDN);
	char buf[1000];
	int  length;

	ret = TmcSend(id, &yoko_cmd[0u]);
	if (ret != 0) {
		cout << "Error retrieving model information" << endl;
		exit(EXIT_FAILURE);
	}
	ret = TmcReceive(id, buf, 1000, &length);
	if (ret != 0) {
		cout << "Error receiving model information" << endl;
		exit(EXIT_FAILURE);
	}
	model_info.assign(buf, length);

	return 1;
}

int pm_controller::set_timeout(int pm_timeout){
	int ret;

	ret = TmcSetTimeout(id, pm_timeout); //milliseconds Even if you lengthen the timeout time, performance will not be affected
	if (ret != 0) {
		cout << "Error setting timeout" << endl;
		exit(EXIT_FAILURE);
	}
	
	return 1;
}

int pm_controller::set_mode(string pm_mode){
	int ret;
	string yoko_cmd;
	string mode(pm_mode);

	if (mode.compare(K_mode_dc) == 0){
		yoko_cmd.assign(YCMD_MODE_DC);
	}
	else if (mode.compare(K_mode_rms) == 0){
		yoko_cmd.assign(YCMD_MODE_RMS);
	}
	else{
		cout << "Invalid mode" << endl;
		exit(EXIT_FAILURE);
	}

	ret = yoko_send(yoko_cmd);

	/*ret = TmcSend(id, &yoko_cmd[0u]);
	if (ret != 0) {
		cout << "Error setting mode" << endl;
		exit(EXIT_FAILURE);
	}*/

	return 1;
}

int pm_controller::set_display(int item_number, string pm_function){
	int ret;
	string yoko_cmd;

	yoko_cmd.assign(YCMD_DISPLAY);
	yoko_cmd.append(to_string(item_number));
	yoko_cmd.push_back('\t');
	yoko_cmd.append(pm_function);

	ret = yoko_send(yoko_cmd);

	return 1;
}

int pm_controller::set_itemx(e_wt_functions item_number, string pm_function){
	int ret;
	string yoko_cmd;
	/*Set itemx*/
	yoko_cmd.assign(YCMD_ITEMX);
	yoko_cmd.append(to_string(item_number));
	yoko_cmd.push_back('\t');
	yoko_cmd.append(pm_function);

	ret = yoko_send(yoko_cmd);
	/*ret = TmcSend(id, &yoko_cmd[0u]);
	if (ret != 0) {
		cout << "Error setting itemx" << endl;
		exit(EXIT_FAILURE);
	}*/

	return 1;
}

int pm_controller::rst_ctl(){
	int ret;
	/* sending *RST */
	string yoko_cmd(YCMD_RST);
	ret = TmcSend(id, &yoko_cmd[0u]);
	/* Wait for a second*/
	std::this_thread::sleep_for(std::chrono::seconds(2));
	return ret;
}

int pm_controller::update_element(pm_parameters& params_t, e_wt_functions item){
	int ret;
	vector<double> val_vect;

	val_vect.push_back(read_value(item));
	params_t.push_value(val_vect, item);

	return 1;
}

int pm_controller::update_data_memory(pm_parameters& params_t){
	int ret;

	ret = update_element(params_t, t_voltage);
	ret = update_element(params_t, t_current);
	ret = update_element(params_t, t_power);
	ret = update_element(params_t, t_energy);
	ret = update_element(params_t, t_itime);

	return 1;
}


int pm_controller::poll_data(pm_settings const& settings_t, pm_parameters& params_t){
	int ret;
	int update_rate = settings_t.data_update_interval;
	int timeout = settings_t.log_duration;
	mytime polltime;

	while ((polltime.elapsed_seconds() < timeout) && (integrator_state() == i_start)){
		update_data_memory(params_t);
		/* Write to output file */
		params_t.write_csv_cont(settings_t.csv_file);
		/* Wait for data update interval*/
		std::this_thread::sleep_for(std::chrono::seconds(update_rate));
		cout << polltime.elapsed_seconds() << "seconds" << endl;
	}

	/*Read remnants*/
	update_data_memory(params_t);
	/* Write to output file */
	params_t.write_csv_cont(settings_t.csv_file);
	/* Wait for data update interval*/
	std::this_thread::sleep_for(std::chrono::seconds(update_rate));
	cout << polltime.elapsed_seconds() << "seconds" << endl;

	return 1;
}