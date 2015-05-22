#!/usr/bin/env python
usage_text = """
LPIRC Powermeter Client
=======================
@2015 - HELPS, Purdue University


Main Tasks:
-----------
1. Communicate with powermeter driver (.exe)
2. Post powermeter readings to the server at the end of the timeout.

Requirements:
-------------
1. Windows
2. Python v2.7.3
3. Powermeter driver (WT310.exe)
4. Yokogawa powermeter windows library (*.dll)
   Ref: https://y-link.yokogawa.com/YL008/?V_ope_type=Show&Download_id=DL00002096&Language_id=EN
   - tmctl.dll
   - ykusb.dll

Usage:
------
referee.py [OPTION]...
Options:
         -w, --pmip
                IP address of the powermeter in format <xxx.xxx.xxx.xxx>
                Default: 192.168.1.3

         --pmexe
                Powermeter driver executable
                Default: ./WT310.exe

         --pminf
                Powermeter interface [ETHERNET | USB]
                Default: ETHERNET

         --pmcsv
                Powermeter poll log
                Default: ./wt310.csv

         --pmmode
                Powermeter mode [RMS | DC]
                Default: DC

         --pminterval
                Powermeter update interval
                Default: 1 second

         --pmtimeout
                Powermeter session timeout in seconds
                Default: 300 seconds (5 Minutes)

         --pm_ping
                Powermeter ping

         --pm_hard_reset
                Powermeter reset (Hardware)

         --pm_soft_reset
                Powermeter reset (Software)

         -h, --help
                Displays all the available option
"""

import getopt, sys, re, glob, os                                          # Parser for command-line options
from datetime import datetime,date,time                                   # Python datetime for session timeout
import shlex                                                              # For constructing popen shell arguments
from subprocess import Popen, PIPE                                        # Non-blocking program execution
import time                                                               # For sleep


#++++++++++++++++++++++++++++++++ Global Variables +++++++++++++++++++++++++++++++++++
this_file_path = os.path.dirname(os.path.abspath(__file__))

# WT310 Powermeter related
pm_executable = os.path.join(this_file_path, 'WT310.exe')
# WT310 Powermeter driver commands
pm_cmd_interface = '--interface'
pm_cmd_ipaddress = '--ip'
pm_cmd_timeout = '--timeout'
pm_cmd_csv = '--csv'
pm_cmd_update_interval = '--interval'
pm_cmd_mode = '--mode'
pm_cmd_hard_reset = '--init'
pm_cmd_start_integration = '--integrate'
# WT310 Powermeter driver arguments
pm_ipaddress = '192.168.1.3'
pm_interface = 'ETHERNET' #ETHERNET | USB    
pm_timeout = 300 #Seconds
pm_csv = os.path.join(this_file_path, 'wt310.csv')
pm_update_interval = 1 #Seconds
pm_mode = 'DC' # DC | RMS
pm_action = None # PING | HARD_RESET | SOFT_RESET

# Powermeter Driver
def powermeter_driver():
    
    pm_command_line = pm_executable + "\t" + \
                      pm_cmd_interface + "\t" + pm_interface + "\t" + \
                      pm_cmd_ipaddress + "\t" + pm_ipaddress + "\t" + \
                      pm_cmd_mode + "\t" + pm_mode + "\t" + \
                      pm_cmd_timeout + "\t" + str(pm_timeout) + "\t" + \
                      pm_cmd_update_interval + "\t" + str(pm_update_interval) 

    if pm_action is not None:
        pm_command_line += "\t--"+pm_action


    if sys.platform == 'win32':
        pm_args = pm_command_line.split()
        print "Executing PM Command:{}\n".format(pm_args)
    else:
        pm_args = shlex.split(pm_command_line)
        print "Executing PM Command:{}\n".format(pm_args)

    # Execute command
    try:
        p = Popen(pm_args, stdin = None, stdout = PIPE, stderr = PIPE, shell = False)
    except:
        print "Power meter communication error\n"
        sys.exit(2) # Abnormal termination

    output = p.communicate()[0]
    print(p.returncode)

    if p.returncode != 0:
        print "Powermeter driver error\n"
        sys.exit(2)

    return

    

# Script usage function
def usage():
    print usage_text


#++++++++++++++++++++++++++++++++ Parse Command-line Input +++++++++++++++++++++++++++++++
# Main function to parse command-line input and run server
def parse_cmd_line():

    global pm_executable
    global pm_ipaddress
    global pm_interface
    global pm_timeout
    global pm_csv
    global pm_update_interval
    global pm_mode
    global pm_action
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hw:", ["help", "pmip=", "pmexe=", "pminf=", "pmcsv=", \
                                                         "pminterval=", "pmmode=", \
                                                         "pm_ping", "pm_hard_reset", "pm_soft_reset", \
                                                         "pmtimeout="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) 
        usage()
        sys.exit(2)
    for switch, val in opts:
        if switch in ("-h", "--help"):
            usage()
            sys.exit()
        elif switch in ("-w", "--pmip"):
            pm_ipaddress = val
        elif switch == "--pmexe":
            pm_executable = os.path.join(this_file_path, val)
        elif switch == "--pminf":
            pm_interface = val
        elif switch == "--pmcsv":
            pm_csv = os.path.join(this_file_path, val)
        elif switch == "--pminterval":
            pm_update_interval = int(val)
        elif switch == "--pmmode":
            pm_mode = val
        elif switch == "--pmtimeout":
            pm_timeout = int(val)
        elif switch == "--pm_ping":
            pm_action = "PING"
        elif switch == "--pm_hard_reset":
            pm_action = "HARD_RESET"
        elif switch == "--pm_soft_reset":
            pm_action = "SOFT_RESET"
        else:
            assert False, "unhandled option"

    print "\npm_exe = "+pm_executable+\
        "\npm_ipaddress = "+pm_ipaddress+\
        "\npm_interface = "+pm_interface+\
        "\npm_csv = "+pm_csv+\
        "\npm_mode = "+pm_mode+\
        "\npm_update_interval (seconds) = "+str(pm_update_interval)+\
        "\npm_timeout (seconds) = "+str(pm_timeout)+\
        "\npm_action = "+str(pm_action)+\
        "\n"


#++++++++++++++++++++++++++++++++ Script enters here at beginning +++++++++++++++++++++++++++++++++++
if __name__ == "__main__":
    # Parse Command-line
    parse_cmd_line()
    # Call powermeter driver
    powermeter_driver()
    sys.exit() # Successful termination: Default 0
else:
    # Parse XML Config file
    print "XML Parsing not found\n"
    # parse_xml_config()
    # # Initialize global variables
    # init_global_vars()
    sys.exit() # Successful termination: Default 0
