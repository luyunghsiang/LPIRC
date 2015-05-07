////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Functionality: Operates the Power Meter. Accepts the IP address and the Task in the argument and performs                  //
//                corresponding tasks.                                                                                        //
//                                                                                                                            //
// Tasks:                                                                                                                     //  
//      INITIALIZE: Initalize WT310.                                                                                          //
//      START     : Starts Integration in the Power Meter.                                                                    //
//      STOP      : Stops Integration in the Power Meter.                                                                     //
//      GET_ENERGY: Gets the integrated power and the Time Elapsed.                                                           //
//      RESET     : Resets WT310.                                                                                             //
//      HELP      : Prints Usage of this program.                                                                             //
//                                                                                                                            //
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// File Needed:
// tmctl.h
// tmctl.dll
// PDFs are in C:\Users\Admin\Desktop\Yokogawa\English
// Project is in C:\Users\Admin\Desktop\Yokogawa\Yokogawa\ConsoleApplication

// To Do:
// 1. Do we need current and Voltage as well? No
// 2. Store with higher resolution and measure how power varies over time.
// 3. The Energy consumed needs to be returned, that will be WH/T
// 4. The time is verified, The WH as of now comes to be zero as nothing was connected.

#include <stdio.h>
#include <Windows.h>
#include <string>
#include "tmctl.h"
#define INITIALIZE 0
#define START 1
#define STOP 2
#define GET_ENERGY 3
#define RESET 4
#define HELP 5
#define BUFSZ 50
#define SUCCESS 99999999
#define TIMEOUT 300
// Enable ARG to accept arguments instead of running the script
#define ARG
using namespace std;

int stop_integration(int*);
int ExecuteCommunicate(int*);
int reset(int*);
int initialize(char*, int*);
int start_integration(int*);
int query_integration_setting(int*);
int get_energy(int*, string *);


// Code Enters Here
int main(int argc, char* argv[] )
{

	int WORK = INITIALIZE,id;

	// Connect the WT310 with ethernet and see the IP address using the interface option.
	char IP_Address[] = "128.46.75.206";
	string WH[2];
	#ifdef ARG
		if (argc > 1)
			strcpy_s(IP_Address,argv[1]);
		if (argc > 2)
			WORK = atoi(argv[2]);
		else
		{
			printf("Usage of the program is :-\n");
			printf("\t./a.exe IP_Address WORK\n");
			printf("\t\tWORK = > \n");
			printf("\t\t\tINITIALIZE: %d\n",INITIALIZE);
			printf("\t\t\tSTART Integration: %d\n",START);
			printf("\t\t\tSTOP Integration: %d\n",STOP);
			printf("\t\t\tGET_ENERGY: %d\n", GET_ENERGY);
			printf("\t\t\tRESET: %d\n",RESET);
			printf("\t\t\tHELP: %d\n", HELP);
		}
		if (WORK == INITIALIZE)
		{
			if (initialize(IP_Address, &id) == SUCCESS) 
				printf("Initialized the WT310\n");
			else return -1;
		}
		if (WORK == START)
		{
			if (start_integration(&id) == SUCCESS) 
				printf("Started Integration\n");
			else return -1;
		}
		if (WORK == STOP)
		{
			if (stop_integration(&id) == SUCCESS) 
				printf("Stopped Integration\n");
			else return -1;
		}
		if (WORK == GET_ENERGY)
		{
			if (get_energy(&id,WH)==SUCCESS)
				printf("WH = %sTIME = %s\n", WH[0].c_str(), WH[1].c_str());
			else return -1;
		}
		if (WORK == RESET)
		{	
			if (reset(&id) == SUCCESS) printf("Reset\n");
			else return -1;
		}
		if (WORK == HELP)
		{
			printf("Usage of the program is :-");
			printf("\t./a.exe IP_Address WORK\n");
			printf("\t\tWORK = > \n");
			printf("\t\t\tINITIALIZE: %d\n", INITIALIZE);
			printf("\t\t\tSTART Integration: %d\n", START);
			printf("\t\t\tSTOP Integration: %d\n", STOP);
			printf("\t\t\tGET_ENERGY: %d\n", GET_ENERGY);
			printf("\t\t\tRESET: %d\n", RESET);
			printf("\t\t\tHELP: %d\n", HELP);
		}
	
	// Script to test the code and functions.
	#else
	// Initialize the WT310 with IP address and id.
	if (initialize(IP_Address, &id) == SUCCESS) 
			printf("Initialized the WT310\n");
	else return -1;

	// Reset WT310
	if (reset(&id) == SUCCESS)
		printf("Reset\n");
	else return -1;
	
	// Query the integration settings.
	if (query_integration_setting(&id) != SUCCESS) 
		return -1;

	// Begin the integration of power.
	if (start_integration(&id) == SUCCESS)
		printf("Started Integration\n");
	else return -1;
	
	// Get the Integrated power and time elapsed.
	// Enter 's' to exit the loop and stop integration, Anything else will continue the loop.
	while (1)
	{
		if (get_energy(&id, WH) == SUCCESS)
			printf("WH = %sTIME = %s\n", WH[0].c_str(), WH[1].c_str());
		else printf("ERROR\n");
		if (getchar() == 's') break;
	}

	// Stop the integration
	if (stop_integration(&id) == SUCCESS)
		printf("Stopped Integration\n");
	else return -1;
	getchar();

	// Query integrated power and time elapsed.
	if (get_energy(&id,WH)==SUCCESS)
		printf("WH = %sTIME = %s\n", WH[0].c_str(), WH[1].c_str());
	else 
	{
		printf("ERROR\n");
		return -1;
	}
	#endif

	getchar();
	//ExecuteCommunicate(&id);
	return 1;
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Function Name: get_energy                                                                                          //
//                                                                                                                    //
// Functionality: Sets Item1 and Item2 as integrated power "WH" and time.                                             //
//                Queries and returns integrated power "WH" and time elapsed between start                            //
//                of integration and stop of integration. If there was no Stop corresponding                          //
//                to previous start, Time returned is time elapsed from previous start in seconds.                    //
//                                                                                                                    //
//  Input:        id: Pointer to the id.                                                                              //
//				  WH: Array of string with                                                                            //
//                    WH[0]: Integrated power in WH.                                                                  //
//					  WH[1]: Time elapsed.                                                                            //
//                                                                                                                    //
//  Output:       Error: If the transactions were unsuccessful, error number is returned.                             //
//                SUCCESS: If the transaction was successful, SUCCESS is returned.                                    //
//                                                                                                                    //
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

int get_energy(int *id, string* WH)
{
	char buf[BUFSZ] = {0};
	int length, ret;

	// Set Item1 as WH
	ret = TmcSend(*id, ":NUMERIC:NORMAL:ITEM1 WH,1");
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}

	//Set Item2 as Time
	ret = TmcSend(*id, ":NUMERIC:NORMAL:ITEM2 TIME,1");
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}

	// Query Power Integrated (WH)
	ret = TmcSend(*id, ":NUMERIC:NORMAL:VALUE? 1");
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}

	ret = TmcReceive(*id, buf, 1000, &length);
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	WH[0] = (string)buf;

	// Query Time of integration
	ret = TmcSend(*id, ":NUMERIC:NORMAL:VALUE? 2");
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	ret = TmcReceive(*id, buf, 1000, &length);
	if (ret != 0) {
			return	TmcGetLastError(*id);
	}
	WH[1] = (string)buf;
	return(SUCCESS);
}


///////////////////////////////////////////////////////////////////////////////////////////////////
// Function Name: query_integration_setting                                                      //
//                                                                                               //
// Functionality: Queries all the integration settings in the power meter and prints it.         //
//                                                                                               //
// Input:        id: Pointer to the id.                                                          //
//                                                                                               //
// Output:       Error: If the transactions were unsuccessful, error number is returned.         //
//               SUCCESS: If the transaction was successful, SUCCESS is returned                 //
//                                                                                               //
///////////////////////////////////////////////////////////////////////////////////////////////////

int query_integration_setting(int *id)
{
	char buf[1000];
	int length;
	int ret = TmcSend(*id, ":INTEGrate?"); // NORM means Standard mode, timer 0 means manual mode.
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	else printf("Sent find integrate settings?\n");
	ret = TmcReceive(*id, buf, 1000, &length);
	if (ret != 0) {
		printf("Error %x\n", TmcGetLastError(*id));
		return	TmcGetLastError(*id);
	}
	else printf("WT returned settings as %s", buf);
	return SUCCESS;
}

//////////////////////////////////////////////////////////////////////////////////////////////////
// Function Name: start_integration                                                             //
//                                                                                              //
// Functionality: Sends the command to start integration on WT310.                              //
//                                                                                              //
//  Input:        id: Pointer to the id.                                                        //
//                                                                                              //
//  Output:       Error: If the transactions were unsuccessful, error number is returned.       //
//                SUCCESS: If the transaction was successful, SUCCESS is returned               //
//                                                                                              //
//////////////////////////////////////////////////////////////////////////////////////////////////

int start_integration(int* id)
{
	int ret = TmcSend(*id, ":INTEGrate:STARt");
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	//else printf("Started integration\n");
	return SUCCESS;
}

//////////////////////////////////////////////////////////////////////////////////////////////////
// Function Name: stop_integration                                                              //
//                                                                                              //
// Functionality: Sends the command to stop integration on WT310.                               //
//                                                                                              //
//  Input:        id: Pointer to the id.                                                        //
//                                                                                              //
//  Output:       Error: If the transactions were unsuccessful, error number is returned.       //
//                SUCCESS: If the transaction was successful, SUCCESS is returned               //
//                                                                                              //
//////////////////////////////////////////////////////////////////////////////////////////////////

int stop_integration(int* id)
{
	int ret = TmcSend(*id, ":INTEGrate:STOP");
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	else printf("Stopped integration\n");
	return SUCCESS;
}

//////////////////////////////////////////////////////////////////////////////////////////////////
// Function Name: reset                                                                         //
//                                                                                              //
// Functionality: Sends the command to reset WT310.                                             //
//                                                                                              //
//  Input:        id: Pointer to the id.                                                        //
//                                                                                              //
//  Output:       Error: If the transactions were unsuccessful, error number is returned.       //
//                SUCCESS: If the transaction was successful, SUCCESS is returned               //
//                                                                                              //
//////////////////////////////////////////////////////////////////////////////////////////////////

int reset(int* id)
{
	int ret;
	ret = TmcSend(*id, "*RST");
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	else printf("Sent RST\n");
	return SUCCESS;
}

//////////////////////////////////////////////////////////////////////////////////////////////////
// Function Name: initialize                                                                    //
//                                                                                              //
// Functionality: Initializes WT310, Sets timeout value, Enables Remote Access, and resets.     //
//                                                                                              //
//  Input:        id: Pointer to the id.                                                        //
//                                                                                              //
//  Output:       Error: If the transactions were unsuccessful, error number is returned.       //
//                SUCCESS: If the transaction was successful, SUCCESS is returned               //
//                                                                                              //
//////////////////////////////////////////////////////////////////////////////////////////////////

int initialize(char* IP_Address, int* id)
{
	printf("Starting to Initialize\n");
	char adr[100];
	int  ret;
	char buf[1000];
	int  length;
	// Initialize
	ret = TmcInitialize(TM_CTL_VXI11, IP_Address, id);
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	else printf("Initialization Successful\n");
	ret = TmcSetTerm(*id, 2, 1);
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	// Setting Time-out
	ret = TmcSetTimeout(*id, TIMEOUT);
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	// Remote Enable
	ret = TmcSetRen(*id, 1);
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	// sending Reset 
	ret = TmcSend(*id, "*RST");
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	return(SUCCESS);
}
int ExecuteCommunicate(int* id)
{
	char adr[100];
	int  ret;
	char buf[1000];
	int  length;
	ret = TmcInitialize(TM_CTL_VXI11, "128.46.75.206", id);
	ret = TmcSetTerm(*id, 2, 1);
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	else printf("Set Term Done\n");
	getchar();
	ret = TmcSetTimeout(*id, 300);
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	else printf("Time Out Set\n");
	ret = TmcSetRen(*id, 1);
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	else printf("Set Ren Done\n");
	getchar();
	/* sending *RST */
	ret = TmcSend(*id, "*RST");
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	else printf("Sent RST\n");
	getchar();
	/* *sending IDN? & receiving query */
	ret = TmcSend(*id, "*IDN?");
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	else printf("Set sent IDN?\n");
	getchar();
	ret = TmcReceive(*id, buf, 1000, &length);
	if (ret != 0) {
		printf("Error %x\n", TmcGetLastError(*id));
		return	TmcGetLastError(*id);
	}
	else printf("Received Something?\n");
	printf("Instrument Model is %s\n", buf);
	/* *sending commands & receiving query */
	getchar();
	ret = TmcSend(*id, ":INPUT:MODE DC");
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	else printf("Sent input mode dc\n");
	getchar();

	/* *sending commands & receiving query */
	ret = TmcSend(*id, ":NUMERIC:NORMAL:ITEM1 WH,1");
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	else printf("Sent numeric normal\n");
	getchar();
	/* *sending commands & receiving query */
	ret = TmcSend(*id, ":NUMERIC:NORMAL:VALUE?");
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	ret = TmcReceive(*id, buf, 1000, &length);
	if (ret != 0) {
		return	TmcGetLastError(*id);
	}
	printf("Received in the end is %s\n", buf);
	getchar();
}