usage_text = """
LPIRC Client 
====================
@2015 - HELPS, Purdue University

Main Tasks:
-----------
1. Login to the Server and store the token generated.
2. Requests for images from server and stores them in directory.
3. POSTS multiple result lines to the server in the form of result.

Requirements:
-------------
1. Python v2.7.3
2. PycURL

Usage:
------
client.py [OPTION]...
Options:
         -w, --ip
                IP address of the server in format <xxx.xxx.xxx.xxx>
                Default: 127.0.0.1

         -p, --port
                Port number of the server.
                Default: 5000

         --user
                Username
                Default: lpirc

         --pass
                Password for the username
                Default: pass
		
	      --dir
		Directory with respect to the client directory 
                where received images are stored
		Default: images

          --in
		Name of the golden csv file to take the input w.r.t. source directory
		Default: golden_output.csv


        --score
		Score that you want to have. The client curropts 
		the golden input with probability (100 - score)/100.
		Default: 100

         -h, --help
                Displays all the available option


"""

from random import randint
import pycurl
import csv
from collections import defaultdict
import getopt,sys
try:
    # python 3
    from urllib.parse import urlencode
except ImportError:
    # python 2
    from urllib import urlencode

from StringIO import StringIO as BytesIO
from StringIO import StringIO

level = 0
columns = defaultdict(list)
lines=""
def get_lines (no_of_lines):
	global score
	global level
	global lines
	if (level+no_of_lines>len(columns[0]) and level<len(columns[0])):
		no_of_lines = len(columns[0])-level
		lines = {'image_name':columns[0][level:level+no_of_lines],'CLASS_ID':columns[1][level:level+no_of_lines],'confidence':columns[2][level:level+no_of_lines],'xmin':columns[3][level:level+no_of_lines],'ymin':columns[4][level:level+no_of_lines],'xmax':columns[5][level:level+no_of_lines],'ymax':columns[6][level:level+no_of_lines]}
		level = len(columns[0])
	elif (level+no_of_lines<=len(columns[0])):
		lines = {'image_name':columns[0][level:level+no_of_lines],'CLASS_ID':columns[1][level:level+no_of_lines],'confidence':columns[2][level:level+no_of_lines],'xmin':columns[3][level:level+no_of_lines],'ymin':columns[4][level:level+no_of_lines],'xmax':columns[5][level:level+no_of_lines],'ymax':columns[6][level:level+no_of_lines]}
		level = level + no_of_lines


def get_image(token, number):
	global image_directory
	c = pycurl.Curl()
	c.setopt(c.URL, host_ipaddress+':'+host_port+'/image/?image='+str(number))
	post_data = {'token':token}
	postfields = urlencode(post_data)
	c.setopt(c.POSTFIELDS,postfields)
	with open('../'+image_directory+'/'+str(number)+'.jpg', 'w') as f:
    		c.setopt(c.WRITEDATA, f)
    		c.perform()
    		c.close()

def post_result(token, data):
	c = pycurl.Curl()
	c.setopt(c.URL, host_ipaddress+':'+host_port+'/result')
	post_data = {'token':token}
	postfields = urlencode(post_data)+'&'+urlencode(data,True)
#	print postfields
#	print
	c.setopt(c.POSTFIELDS,postfields)
   	c.perform()
    	c.close()


def read_csv(csv_filename):
	global csv_data
	with open(csv_filename) as csvfile:
		databuf = csv.reader(csvfile, delimiter=' ')
		for row in databuf:
			for (i,v) in enumerate(row):
				columns[i].append(v)
	level = len(columns[0])

def corrupt_csv ():
	no_of_lines = len(columns[0])
	global score
	global level
	global lines
	rand = randint(1,100)
	if (rand >= score):
		print "Wrong entry\n"
		columns[1][0:no_of_lines]=[str(int(x)+5) for x in columns[1][0:no_of_lines]] # adding class number by 5 to corrupt the line

# Script usage function
def usage():
    print usage_text

# Main function to parse command-line input and run server
def parse_cmd_line():

    global host_ipaddress
    global host_port
    global score
    global username
    global password
    global csv_filename
    global image_directory
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hw:p:", ["help", "ip=", "port=", "user=", "pass=", "in=", "dir=", "score="])
    except getopt.GetoptError as err:
        print str(err) 
        usage()
        sys.exit(2)
    for switch, val in opts:
        if switch in ("-h", "--help"):
            usage()
            sys.exit()
        elif switch in ("-w", "--ip"):
            host_ipaddress = val
        elif switch in ("-p", "--port"):
            host_port = val
        elif switch == "--user":
            username = val
        elif switch == "--pass":
            password = val
	elif switch in ("-i","--in"):
	    csv_filename = val
	elif switch == "--dir":
	    image_directory = val
	elif switch in ("-s","--score"):
	    score = int(val)
        else:
            assert False, "unhandled option"

    print "\nhost = "+host_ipaddress+":"+host_port+"\nUsername = "+username+"\nPassword = "+password+"" 


# Parse Command-line
host_ipaddress = '127.0.0.1'
host_port = '5000'
password = 'pass'
score = 100
username = 'lpirc'
csv_filename = 'golden_output.csv'
image_directory = 'images'
parse_cmd_line()

#login
buffer = StringIO()
c = pycurl.Curl()
c.setopt(c.URL, host_ipaddress+':'+host_port+'/login')
post_data = {'username':username,'password':password}
postfields = urlencode(post_data)
c.setopt(c.POSTFIELDS,postfields)
c.setopt(c.WRITEFUNCTION, buffer.write)
c.perform()
c.close()

token = buffer.getvalue()
# Body is a string in some encoding.
# In Python 2, we can print it without knowing what the encoding is.
#print(token)


read_csv(csv_filename)
corrupt_csv()

for w in range (1,9,3):
	get_image(token,w)
	get_image(token,w+1)
	get_image(token,w+2)
	get_lines(1)
	post_result(token,lines)
	get_lines(2)
	post_result(token,lines)

