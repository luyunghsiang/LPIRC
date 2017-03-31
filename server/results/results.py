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
                Used when images are shuffled between teams.

         --rcsv
                Path to the results csv file.

         --user
                User for whom the score is calculated. 

         -h, --help
                Displays all the available option
"""

import getopt, sys, re, glob, os                                          # Parser for command-line options
from subprocess import Popen, PIPE                                        # Non-blocking program execution
import time                                                               # For sleep
import csv                                                                # To process powermeter driver generated csv file
from pyeval import DetectionEvaluate                                      # Evaluation of results

#++++++++++++++++++++++++++++++++ Global Variables +++++++++++++++++++++++++++++++++++
this_file_path = os.path.dirname(os.path.abspath(__file__))
pm_csv = os.path.join(this_file_path, '../powermeter/WT310.csv')
map_csv = os.path.join(this_file_path, '../shuffle/map0.txt')
r_csv = os.path.join(this_file_path, '../csv/tmp/lpirc.csv')
r_interval = 5
r_timeout = 300
r_user = "lpirc"

# Script usage function
def usage():
    print usage_text

class BoundingBox(object):
    """docstring for BoundingBox"""
    def __init__(self, arg):
        super(BoundingBox, self).__init__()
        self.arg = arg
        self.image_id = int(arg[0])
        self.class_id = int(arg[1])
        self.confidence = float(arg[2])
        self.xmin = float(arg[3])
        self.ymin = float(arg[4])
        self.xmax = float(arg[5])
        self.ymax = float(arg[6])

    def __iter__(self):
        return(iter([self.class_id, self.confidence, self.xmin, self.ymin, self.xmax, self.ymax]))

    def __str__(self):
        return "{}".format([self.class_id, self.confidence, self.xmin, self.ymin, self.xmax, self.ymax])

class Image(object):
    """docstring for Image"""
    def __init__(self, arg):
        super(Image, self).__init__()
        self.arg = arg
        self.image_id = int(arg[0])
        self.bboxes = [BoundingBox(arg)]

    def __iter__(self):
        return iter([list(x) for x in self.bboxes])

    def __dict__(self):
        return {self.image_id:self}

    def __str__(self):
        return "Image:\nID:{}\nBounding Boxes:{}".format(self.image_id, [str(x) for x in self.bboxes])

    def addBbox(self, arg):
        newBox = BoundingBox(arg)
        if newBox not in self.bboxes:
            self.bboxes.append(newBox)

#++++++++++++++++++++++++++++++++ Computing Results +++++++++++++++++++++++++++++++
# Computes results after every interval by calling the evaluation program
def compute_results ():
    # Specify the needed files. We need to replace these files.
    det_meta_file = os.path.join (this_file_path, "data", "meta_det.mat")
    det_eval_file = os.path.join (this_file_path, "data", "val.txt")
    det_gt_file = os.path.join (this_file_path, "data", "det_validation_ground_truth.mat")
    det_blacklist_file = os.path.join (this_file_path, "data", "det_validation_blacklist.txt")
    demo_val_det_file = r_csv
    last_ind = 0
    prev_last_ind = -1
    ap = 0

    # Initialize a EvaluateDetection object. Do it one time at the begining.
    det_eval = DetectionEvaluate(
        det_meta_file, det_eval_file, det_gt_file, det_blacklist_file)

    time_elapsed = 0
    pm_file = open(pm_csv, 'r')
    map_file = open(map_csv, 'r')
    detections = dict()

    while time_elapsed <= r_timeout:
        start_t = time.clock ()
        time.sleep (r_interval)
        f = open(demo_val_det_file, "r")
        lines = f.readlines()
        f.close ()
        pick_lines = range (last_ind, len (lines))
        print(len(pick_lines))
        # return
        if last_ind < len (lines):
            for line in lines:
                # line = lines[i]
                items = line.rstrip("\n").split(",")
                # img = Image(items)
                image_id = int(items[0])
                # bbox = img.bboxes
                # if img.image_id not in detections.keys(): 
                    # detections.update(img.__dict__())

                if image_id in detections:
                    detections[image_id].addBbox(items)
                else:
                    detections[image_id] = Image(items)
        
        prev_last_ind = last_ind
        # last_ind = pick_lines[len(lines)-1] + 1
        print detections[1]
        ap = det_eval.evaluate(detections)

        print "evaluated", prev_last_ind, last_ind, len(lines)
        # if (prev_last_ind != last_ind):


        pm_lines = tail (pm_file, 1)
        pm_vals = pm_lines.rstrip("\n").split(",")
        if float (pm_vals[-2]) > 0:
            print r_user, "power =", pm_vals[-2], "mAP =", ap, "score =", (ap / float (pm_vals[-2]))
        #print "last_ind =", last_ind, "prev_last_ind =", prev_last_ind, "ap =", ap, "len of dict =", len(detections)
        #print pm_lines
        time_elapsed += r_interval

    pm_file.close ()
    map_file.close ()
        
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
    global r_csv
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hw:", ["help", "pmcsv=", "mapcsv=",\
                                                         "interval=", "timeout=", "rcsv="])
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
            pm_csv = os.path.join(this_file_path + "/../powermeter/", val)
        elif switch == "--mapcsv":
            map_csv = os.path.join(this_file_path + "/../shuffle/", val)
        elif switch == "--interval":
            r_interval = int(val)
        elif switch in ("-t", "--timeout"):
            r_timeout = int(val)
        elif switch == "--rcsv":
            r_csv = os.path.join(this_file_path + "/../csv/tmp/", val)
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
    #time.sleep (r_interval)
    compute_results()
else:
    # Parse XML Config file
    print "XML Parsing not found\n"
    # parse_xml_config()
    # # Initialize global variables
    # init_global_vars()
    sys.exit() # Successful termination: Default 0