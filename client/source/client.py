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



#++++++++++++++++++++++++++++ get_token: Can be used by the participant directly ++++++++++++++++++++++++++++++++++
# 
# Functionality : 
# Sends request to the server to log in with username and password and returns the token. 
# token needs to be used in all the communication with the server in the session. 
# 
# Usage: token = get_token(username, password)
# 
# Inputs: 
#         1. username
#         2. password
#
# Outputs:
#         1. token
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def get_token (username,password):

	buffer = StringIO()
	c = pycurl.Curl()
	c.setopt(c.URL, host_ipaddress+':'+host_port+'/login')
	post_data = {'username':username,'password':password}
	postfields = urlencode(post_data)
	c.setopt(c.POSTFIELDS,postfields)
	c.setopt(c.WRITEFUNCTION, buffer.write)
	c.perform()
	c.close()
	return buffer.getvalue()


#++++++++++++++++++++++++++++ get_image: Can be used by the participant directly ++++++++++++++++++++++++++++++++++
# 
# Functionality : 
# Sends request to the server for an image with its token number and the image number 
# 
# Usage: get_image(token, number)
# 
# Inputs: 
#         1. token : Obtained from Log in ( get_token() )
#         2. image_number : Index of image client needs.
#
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def get_image(token, image_number):
	global image_directory
	c = pycurl.Curl()
	c.setopt(c.URL, host_ipaddress+':'+host_port+'/image/?image='+str(image_number))
	post_data = {'token':token}
	postfields = urlencode(post_data)
	c.setopt(c.POSTFIELDS,postfields)
	with open('../'+image_directory+'/'+str(image_number)+'.jpg', 'w') as f:
    		c.setopt(c.WRITEDATA, f)
    		c.perform()
    		c.close()

#++++++++++++++++++++++++++++ post_result: Can be used by the participant directly ++++++++++++++++++++++++++++++++++
# 
# Functionality : 
# Posts the bounding box information corresponding to an image back to the server. 
# 
# Usage: get_image(token, data)
# 
# Inputs: 
#         1. token: Obtained from Log in
#         2. data : data is a dictionary which stores multiple bounding box information lines.
#                   Bounding box information line consists of 7 parameters:
#		    a. image_name: Image index 
#		    b. CLASS_ID: 
#		    c. confidence
#		    d. ymax
#		    e. xmax
#		    f. xmin
#		    g. ymin
#		    
#		    data is a dictionary with:
#			key:     'image_name', 'CLASS_ID', 'confidence', 'ymax', 'xmax', 'xmin', 'ymin'
#			values:  list of values corresponding to the keys
#
#		    Eg: data for 2 lines of images 1 and 2 resp. would be:-
#
#			data = {'image_name': ['1', '2'], 'CLASS_ID': ['58', '10'],'confidence': ['0.529047', '0.184961'],
#				'ymax': ['271.055408', '225.339863'],  'xmax': ['351.519712', '194.408771'],
#				'xmin': ['291.439033', '184.804591'], 'ymin': ['237.148035', '212.047943']}
#                   
#			The first value corresponds to image 1 and second value to image 2.
#
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def post_result(token, data):
	c = pycurl.Curl()
	c.setopt(c.URL, host_ipaddress+':'+host_port+'/result')
	post_data = {'token':token}
	postfields = urlencode(post_data)+'&'+urlencode(data,True)
	c.setopt(c.POSTFIELDS,postfields)
   	c.perform()
    	c.close()

#++++++++++++++++++++++++++++ get_lines: Internal Function ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# 
# Functionality : 
# Pops bounding box lines from the directory and returns 
# 
# Usage: get_lines(no_of_lines)
# 
# Inputs: 
#         1. no_of_lines: Number of lines to pop and return
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def get_lines (no_of_lines):
	global score
	global level
	if (level+no_of_lines>len(columns[0]) and level<len(columns[0])):
		no_of_lines = len(columns[0])-level
		lines = {'image_name':columns[0][level:level+no_of_lines],'CLASS_ID':columns[1][level:level+no_of_lines],'confidence':columns[2][level:level+no_of_lines],'xmin':columns[3][level:level+no_of_lines],'ymin':columns[4][level:level+no_of_lines],'xmax':columns[5][level:level+no_of_lines],'ymax':columns[6][level:level+no_of_lines]}
		level = len(columns[0])
	elif (level+no_of_lines<=len(columns[0])):
		lines = {'image_name':columns[0][level:level+no_of_lines],'CLASS_ID':columns[1][level:level+no_of_lines],'confidence':columns[2][level:level+no_of_lines],'xmin':columns[3][level:level+no_of_lines],'ymin':columns[4][level:level+no_of_lines],'xmax':columns[5][level:level+no_of_lines],'ymax':columns[6][level:level+no_of_lines]}
		level = level + no_of_lines

	return lines


#++++++++++++++++++++++++++++ read_csv: Internal Function ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# 
# Functionality : 
# 
# Reads a file with the results in the form separated with a space and generates database.
# Format of the file:-
# 
# <image_name> <CLASS_ID> <confidence> <xmin> <ymin> <xmax> <ymax>
# <image_name> <CLASS_ID> <confidence> <xmin> <ymin> <xmax> <ymax>
# ...
# ...
# 
# Usage: get_lines(no_of_lines)
# 
# Inputs: 
#         1. no_of_lines: Number of lines to pop and return
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def read_csv(csv_filename):
	global csv_data
	with open(csv_filename) as csvfile:
		databuf = csv.reader(csvfile, delimiter=' ')
		for row in databuf:
			for (i,v) in enumerate(row):
				columns[i].append(v)
	level = len(columns[0])

#++++++++++++++++++++++++++++ corrupt_csv: Internal Function ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# 
# Functionality : 
# Corrupts the database: It changes the CLASS_ID field of a line randomly picked with probability (1 - score/100)
# 
# Usage: corrupt_csv(score)
# 
# Inputs: 
#         1. score: Score [0,100] which needs to be obtained.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def corrupt_csv (score):
	no_of_lines = len(columns[0])
	global level
	global lines
	for w in range(0,no_of_lines):
		rand = randint(1,100)
		if (rand >= score):
			columns[1][w]=str(int(columns[1][w])+5) # adding class number by 5 to corrupt the line




#+++++++++++++++++++++++++++ Script usage function +++++++++++++++++++++++++++++++++++++++++++++++++++
def usage():
    print usage_text

#++++++++++++++++++++ Main function to parse command-line input and run server ++++++++++++++++++++++++++++
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


#+++++++++++++++++++++++++++ Global Variables ++++++++++++++++++++++++++++++++++++++++++++++++++++
host_ipaddress = '127.0.0.1'
host_port = '5000'
password = 'pass'
score = 100
username = 'lpirc'
csv_filename = 'golden_output.csv'
image_directory = 'images'


#+++++++++++++++++++++++++++ Start of the script +++++++++++++++++++++++++++++++++++++++++++++++
parse_cmd_line()

token = get_token(username,password)   # Login to server and obtain token
read_csv(csv_filename)                 # Read the csv file to obtain the data
corrupt_csv(score)                     # Corrupt the database read to obtain a score of 'score'

for w in range (1,10,3):
	get_image(token,w)             # get image in the assigned directory with index 'w'
	get_image(token,w+1)
	get_image(token,w+2)
	get_image(token,w+3)
	lines = get_lines(1)           # pop 1 line from the data base and store it in 'lines'
	post_result(token,lines)       # post 'lines' to the server along with the token
	lines = get_lines(2)
	post_result(token,lines)

