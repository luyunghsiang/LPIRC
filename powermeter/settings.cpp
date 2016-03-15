#include <vector>
#include <iostream>
#include "settings.h"
#include "getopt.h"

/* Power Meter Interfaces*/
const string K_inf_ethernet = "ETHERNET";
const string K_inf_usb = "USB";
/* Power Meter Modes*/
const string K_mode_dc = "DC";
const string K_mode_rms = "RMS";

/*Constants for command line arguments*/
string cmd_interface = "interface";
string cmd_ipaddress = "ip";
string cmd_log_duration = "timeout";
string cmd_csv_file = "csv";
string cmd_data_update_interval = "interval";
string cmd_mode = "mode";
string cmd_help = "help";
string cmd_ping = "PING";
string cmd_stop = "STOP";
string cmd_hard_reset("HARD_RESET");
string cmd_soft_reset("SOFT_RESET");

void pm_settings::print_help(){

	cout << "WT310.exe" << "[options]" << endl <<
		"Options:" << endl <<
		"\t--help    Print this help" << endl <<
		"\t--" << cmd_interface << "\t[" << K_inf_ethernet << "|" << K_inf_usb << "]" << endl <<
		"\t--" << cmd_ipaddress << "\t<192.168.1.3>" << endl <<
		"\t--" << cmd_log_duration << "\t<300> seconds" << endl <<
		"\t--" << cmd_csv_file << "\t<wt310.csv>" << endl <<
		"\t--" << cmd_data_update_interval << "\t<1> seconds" << endl <<
		"\t--" << cmd_mode << "\t[" << K_mode_rms << "|" << K_mode_dc << "]" << endl <<
		"\t--" << cmd_ping << "\tPing powermeter" << endl <<
		"\t--" << cmd_hard_reset << "\tPowermeter hard reset" << endl <<
		"\t--" << cmd_soft_reset << "\tPowermeter soft reset" << endl <<
		"\t--" << cmd_stop << "\tPowermeter stop" << endl <<
		endl;
}

pm_settings::pm_settings(){
	stop = 0;
	ping = 0;
	hard_reset = 0;
	soft_reset = 0;
	begin_time = clock();
	ipaddress = "192.168.1.3";
	interface = K_inf_ethernet;
	log_duration = 300;		//seconds
	csv_file = "wt310.csv";
	data_update_interval = 1; //seconds
	mode = K_mode_dc;
}

void pm_settings::print_settings(){
	cout << "Power Meter Settings:" << endl;
	cout << "---------------------" << endl;
	cout << "IP Address:\t" << ipaddress << endl;
	cout << "Interface:\t" << interface << endl;
	cout << "Log Duration:\t" << log_duration << endl;
	cout << "Output File:\t" << csv_file << endl;
	cout << "Data Update Interval:\t" << data_update_interval << endl;
	cout << "Power Meter Mode:\t" << mode << endl;
}

double pm_settings::elapsed_time(){
	clock_t now_time = clock();
	double elapsed_secs = double(now_time - begin_time) / CLOCKS_PER_SEC;
	return elapsed_secs;
}


int pm_settings::parse_cmd_line(int argc, char **argv){
	/* GNU getopt*/
	int c;
	while (1)
	{
		static struct option long_options[] =
		{
			/* These options don’t set a flag.
			We distinguish them by their indices. */
			{ &cmd_interface[0u], required_argument, 0, 'f' },
			{ &cmd_ipaddress[0u], required_argument, 0, 'i' },
			{ &cmd_log_duration[0u], required_argument, 0, 'l' },
			{ &cmd_csv_file[0u], required_argument, 0, 'c' },
			{ &cmd_data_update_interval[0u], required_argument, 0, 'u' },
			{ &cmd_mode[0u], required_argument, 0, 'm' },
			{ &cmd_help[0u], no_argument, 0, 'h' },
			{ &cmd_ping[0u], no_argument, 0, 'p' },
			{ &cmd_stop[0u], no_argument, 0, 'x' },
			{ &cmd_hard_reset[0u], no_argument, 0, 't' },
			{ &cmd_soft_reset[0u], no_argument, 0, 's' },
			{ 0, 0, 0, 0 }
		};
		/* getopt_long stores the option index here. */
		int option_index = 0;

		c = getopt_long(argc, argv, "f:i:l:c:u:m:hpxts",
			long_options, &option_index);

		/* Detect the end of the options. */
		if (c == -1)
			break;

		/* Temp string*/
		string tmps;

		switch (c)
		{
		case 0:
			/* If this option set a flag, do nothing else now. */
			if (long_options[option_index].flag != 0)
				break;
			printf("option %s", long_options[option_index].name);
			if (optarg)
				printf(" with arg %s", optarg);
			printf("\n");
			break;

//"f:i:l:c:u:m:"
		case 'h':
			print_help();
			exit(EXIT_SUCCESS);

		case 'p':
			ping = 1;
			break;

		case 'x':
			stop = 1;
			break;

		case 't':
			hard_reset = 1;
			break;

		case 's':
			soft_reset = 1;
			break;

		case 'l':
			/*Log duration*/
			tmps.assign(optarg);
			log_duration = stoi(tmps);
			break;

		case 'c':
			tmps.assign(optarg);
			csv_file.assign(tmps);
			break;

		case 'u':
			/* Data Update Rate*/
			tmps.assign(optarg);
			data_update_interval = stoi(tmps);
			break;

		case 'm':
			tmps.assign(optarg);
			if ((tmps.compare(K_mode_rms)) && (tmps.compare(K_mode_dc))){
				print_help();
				exit(EXIT_FAILURE);
			}
			mode.assign(tmps);
			break;

		case 'f':
			tmps.assign(optarg);
			if ((tmps.compare(K_inf_ethernet)) && (tmps.compare(K_inf_usb))){
				print_help();
				exit(EXIT_FAILURE);
			}
			interface.assign(tmps);
			break;

		case 'i':
			ipaddress.assign(optarg);
			break;

		default:
			abort();
		}
	}

	/* Print any remaining command line arguments (not options). */
	if (optind < argc){
		cout << "Invalid Option" << endl;
		print_help();
		exit(EXIT_FAILURE);
	}

}
