#!/usr/bin/env python
usage_text = """
LPIRC results program
=====================
@2016 - HELPS, Purdue University

Main Tasks:
-----------
1. Calculate results for the current user and display them.

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
results.py [OPTIONS]...
Options:
         --interval
                Interval (in seconds) at which we need to get readings and
                calculate results. (Default value is 5)
                
         -t, --timeout
                Results session timeout in seconds.
                (Default value is 300)

         --pmcsv
                Path to the powermeter output csv file.

         --mapcsv
                Path to the image map files.

         -h, --help
                Displays all the available option
"""

import getopt, sys, re, glob, os                                          # Parser for command-line options
from subprocess import Popen, PIPE                                        # Non-blocking program execution
import time                                                               # For sleep
import csv                                                                # To process powermeter driver generated csv file

#++++++++++++++++++++++++++++++++ Global Variables +++++++++++++++++++++++++++++++++++
this_file_path = os.path.dirname(os.path.abspath(__file__))
pm_csv = os.path.join(this_file_path, '../powermeter/WT310.csv')
map_csv = os.path.join(this_file_path, '../shuffle/map0.txt')
r_interval = 5
r_timeout = 300

# Script usage function
def usage():
    print usage_text

#++++++++++++++++++++++++++++++++ Computing Results +++++++++++++++++++++++++++++++
# Computes results after every interval by calling the evaluation program
def compute_results ():
    time_elapsed = 0
    pm_file = open (pm_csv, 'r')
    map_file = open (map_csv, 'r')
    while time_elapsed <= r_timeout:
        start_t = time.clock ()
        time.sleep (r_interval)
        lines = tail (pm_file, 1)
        print lines
        time_elapsed += r_interval
        
# Performs similiar to UNIX's tail
def tail( f, lines=20 ):
    total_lines_wanted = lines

    BLOCK_SIZE = 1024
    f.seek(0, 2)
    block_end_byte = f.tell()
    lines_to_go = total_lines_wanted
    block_number = -1
    blocks = [] # blocks of size BLOCK_SIZE, in reverse order starting
                # from the end of the file
    while lines_to_go > 0 and block_end_byte > 0:
        if (block_end_byte - BLOCK_SIZE > 0):
            # read the last block we haven't yet read
            f.seek(block_number*BLOCK_SIZE, 2)
            blocks.append(f.read(BLOCK_SIZE))
        else:
            # file too small, start from begining
            f.seek(0,0)
            # only read what was not read
            blocks.append(f.read(block_end_byte))
        lines_found = blocks[-1].count('\n')
        lines_to_go -= lines_found
        block_end_byte -= BLOCK_SIZE
        block_number -= 1
    all_read_text = ''.join(reversed(blocks))
    return '\n'.join(all_read_text.splitlines()[-total_lines_wanted:])


#++++++++++++++++++++++++++++++++ Parse Command-line Input +++++++++++++++++++++++++++++++
# Main function to parse command-line input
def parse_cmd_line():
    global pm_csv
    global map_csv
    global r_interval
    global r_timeout
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hw:", ["help", "pmcsv=", "mapcsv=",\
                                                         "interval=", "timeout="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) 
        usage()
        sys.exit(2)
    for switch, val in opts:
        if switch in ("-h", "--help"):
            usage()
            sys.exit()
        elif switch == "--pmcsv":
            pm_csv = os.path.join(this_file_path, val)
        elif switch == "--mapcsv":
            map_csv = os.path.join(this_file_path, val)
        elif switch == "--interval":
            r_interval = int(val)
        elif switch in ("-t", "--timeout"):
            r_timeout = int(val)
        else:
            assert False, "unhandled option"

    print "\npm_csv = "+pm_csv+\
        "\nmap_csv = "+map_csv+\
        "\nr_interval = "+str(r_interval)+\
        "\nr_timeout = "+str(r_timeout)+\
        "\n"

#++++++++++++++++++++++++++++++++ Script enters here at beginning +++++++++++++++++++++++++++++++++++
if __name__ == "__main__":
    # Parse Command-line
    parse_cmd_line()
    compute_results()
else:
    # Parse XML Config file
    print "XML Parsing not found\n"
    # parse_xml_config()
    # # Initialize global variables
    # init_global_vars()
    sys.exit() # Successful termination: Default 0