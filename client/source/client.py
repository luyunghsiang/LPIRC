usage_text = """
LPIRC Client 
This is a sample client for illustration purpose only.
This sample client is written in python but a client program can be written in any language, as long as it can communicate using HTTP GET and POST.

====================
@2015 - HELPS, Purdue University

Main Tasks:
-----------
1. Login to the Server and store the token from the server.
2. Request images from the server and store the images in a directory.
3. Send POST messages to the server as the results.
4. Request total number of valid images from server.

Rules:
1. If a single image has multiple bounding boxes, the client can send the bounding boxes in the same POST message.
2. The client may send multiple POST messages for different bounding boxes of the same image.
3. Two different images need to be sent in the different POST messages.
4. The POST messages for different images may be out of order (for example, the bounding boxes for image 5 may be sent before the bounding boxes for image 3)


Steps to Follow to Run the client script:
1. Download client.py and golden_output.csv files from https://github.com/luyunghsiang/LPIRC.git
2. Keep both the files in the same directory.
3. Run the command:

   >python client.py -w 128.46.75.108 --im_dir images --temp_dir temp
	
   This command will start the script by connecting it to the server hosted by lpirc.ecn.purdue.edu
   The script will create two new directories, "temp" and "images", in the same directory as client.py, if they are not already present.
   All the images received from the server will be stored in the "images" directory.

Requirements:
-------------
1. Python v2.7.3
2. PycURL (To support HTTP)

Usage:
------
client.py [OPTION]...
Options:
         -w, --ip
                IP address of the server in format <xxx.xxx.xxx.xxx>
                Default: 128.46.75.108

         -p, --port
                Port number of the server.
                Default: 80

         --user
                Username
                The user must send a mail to lpirc@ecn.purdue.edu to request 
		for a username and password.

         --pass
                Password for the username
                The user must send a mail to lpirc@ecn.purdue.edu to request 
		for a username and password.
		
         --im_dir
		Directory with respect to the client.py 
                where received images are stored
		Default: ../images

	 --temp_dir
		Directory with respect to the client.py
		where temporary data is stored
		Default: ../temp

         --in
		Name of the csv file to take the input with respect to source directory
		Default: golden_output.csv
		(This is for testing purpose only. It should not be in the real client.)

         --score
		Score that you want to have. The client corrupts 
		the golden input with probability (100 - score)/100.
		Default: 100
		(This is for testing purpose only. It should not be in the real client.)

         -h, --help
                Displays all the available option


"""

from random import randint
import pycurl
import csv,shutil,os
from collections import defaultdict
import getopt,sys, time
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



#++++++++++++++++++++++++++++ get_token: Can be used by the participant directly ++++++++++++++++++++
# 
# Functionality : 
# Sends request to the server to log in with username and password and returns the token and status. 
# Token needs to be used in all the communication with the server in the session.
# If the username and password are invalid or the session has expired, status returned is 0.
# If the token is is valid, status returned is 1.
# 
# This must be the first message to the server.
#
# Usage: [token, status] = get_token(username, password)
# 
# Inputs: 
#         1. username
#         2. password
#
# Outputs:
#         1. token
#	  2. status
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def get_token (username,password):

	buffer = StringIO()
	c = pycurl.Curl()
	c.setopt(c.URL, host_ipaddress+':'+host_port+'/login')
	post_data = {'username':username,'password':password}
	postfields = urlencode(post_data)
	c.setopt(c.POSTFIELDS,postfields)
	c.setopt(c.WRITEFUNCTION, buffer.write)
	c.perform()
	status = c.getinfo(pycurl.HTTP_CODE)
	c.close()
	if status == 200:
		return [buffer.getvalue(),1]
	else:
	#	print status
		print "Unauthorised Access\n"
		return [buffer.getvalue(),0]


#++++++++++++++++++++++++++++ get_image: Can be used by the participant directly ++++++++++++++++++++++++++++++++++
# 
# Functionality : 
# Sends request to the server for an image with its token number and the image number.
# 'status' is 1 if the image transfer succeeded. If the transfer failed, 'status' will be set to 0. 
# Transfer can fail because of two reasons:-
# 1. The image_number request is out of the valid range [1,total_image_number] (inclusive)
# 2. The token is not valid.
#
# Usage: status = get_image(token, image_number) 
# Total number of images can be queried from server using get_no_of_images(token).
# If image number is outside the permitted range, penalty will be assigned. 
#
# Inputs: 
#         1. token : Obtained from Log in ( get_token() )
#         2. image_number : Index of image client needs.
#
# Output:
#	  1. status  
#
# Note:
#         The image is buffered in the temp_directory. If the POST message succeeds, 
#         the file is moved to the image_directory. 
#	  This movement can be avoided by buffering the file to image_directory and removing the same if HTTP status is not 200 (OK). 
#
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def get_image(token, image_number):
	global image_directory
	global temp_directory
	c = pycurl.Curl()
	c.setopt(c.URL, host_ipaddress+':'+host_port+'/image')#/?image='+str(image_number))
	post_data = {'token':token, 'image_name':str(image_number)}
	postfields = urlencode(post_data)
	c.setopt(c.POSTFIELDS,postfields)
	try:
    		os.stat(temp_directory)
	except:
    		os.mkdir(temp_directory)
	try:
    		os.stat(image_directory)
	except:
    		os.mkdir(image_directory)
	# Image will be saved as a file
	with open(temp_directory+'/'+str(image_number)+'.jpg', 'wb') as f:
    		c.setopt(c.WRITEDATA, f)
		c.perform()
		status = c.getinfo(pycurl.HTTP_CODE)
		c.close()
	if status == 200:
		# Server replied OK so, copy the image from temp_directory to image_directory
		shutil.move(temp_directory+'/'+str(image_number)+'.jpg',image_directory+'/'+str(image_number)+'.jpg')
		return 1
	elif status == 401:
		# Server replied 401, Unauthorized Access, remove the temporary file
		os.remove(temp_directory+'/'+str(image_number)+'.jpg')
		print "Invalid Token\n"
		return 0
	else:
		# Server replied 406, Not Acceptable, remove the temporary file
		os.remove(temp_directory+'/'+str(image_number)+'.jpg')
		print "The image number is not Acceptable\n" 
		return 0

#++++++++++++++++++++++++++++ post_result: Can be used by the participant directly ++++++++++++++++++++++++++++++++++
# 
# Functionality : 
# POSTS the bounding box information corresponding to an image back to the server. If the POST message to the server 
# succeeded, status = 1. If the POST message to the server failed, the status is set as 0.
# The POST message can fail because of 2 reasons:-
# 1. The token is not valid
# 2. The format of 'data' is incorrect
#
# Usage: post_result(token, data)
# 
# Inputs:
#         1. token: Obtained from Log in
#         2. data :
#		    data is a dictionary container with:
#			key:     'image_name', 'CLASS_ID', 'confidence', 'ymax', 'xmax', 'xmin', 'ymin'
#			values:  list of values corresponding to the keys
#
#		    Eg: data for 2 bounding boxes of images 1 could be:-
#
#			data = {'image_name': ['1', '1'], 'CLASS_ID': ['58', '10'],'confidence': ['0.529047', '0.184961'],
#				'ymax': ['271.055408', '225.339863'],  'xmax': ['351.519712', '194.408771'],
#				'xmin': ['291.439033', '184.804591'], 'ymin': ['237.148035', '212.047943']}
#                   
# Outputs:
#	  1. status
#
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def post_result(token, data):
	c = pycurl.Curl()
	c.setopt(c.URL, host_ipaddress+':'+host_port+'/result')
	post_data = {'token':token}
	postfields = urlencode(post_data)+'&'+urlencode(data,True)
	c.setopt(c.POSTFIELDS,postfields)
   	c.perform()
	status = c.getinfo(pycurl.HTTP_CODE)
	c.close()
	if status == 200:
		# Server replied 200, OK, Result stored
		return 1
	elif (status == 401):
		# Server replied 401, Unauthorized Access
		print "Unauthorized Access\n"
		return 0
	else:
		# Server replied 406, In correct format of 'data'
		print "Not Acceptable. Incorrect Format of result data\n"
		return 0

#++++++++++++++++++++++++++++ get number of images: Can be used by the participant directly ++++++++++++++++++++++++++++++++++
# Functionality : 
# POSTS the message to the server and gets back the total number of images.
# If the server sends back OK status (200), status=1 and 'number_of_images' is valid
# If the server sends Unauthorized Access (401), status=0 and 'number_of_images' is invalid.
# 
# Usage: no_of_images = get_no_of_images(token)
# 
# Inputs:
#         1. token: Obtained from Log in
#
# Output:
#         1. number_of_images
#         2. status
#
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def get_no_of_images(token):
	buffer = StringIO()
	c = pycurl.Curl()
	c.setopt(c.URL, host_ipaddress+':'+host_port+'/no_of_images')
	post_data = {'token':token}
	postfields = urlencode(post_data)
	c.setopt(c.POSTFIELDS,postfields)
   	c.setopt(c.WRITEFUNCTION, buffer.write)
	c.perform()
    	status = c.getinfo(pycurl.HTTP_CODE)
	c.close()
	if status == 200:
		return [buffer.getvalue(), 1]
	else:
		return [buffer.getvalue(), 0]



# The following functions are for testing purpose only. They should not be in the actual client.

#++++++++++++++++++++++++++++ get_lines: Internal Function ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#
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
		lines = {'image_name':columns[0][level:level+no_of_lines],\
				'CLASS_ID':columns[1][level:level+no_of_lines],\
				'confidence':columns[2][level:level+no_of_lines],\
				'xmin':columns[3][level:level+no_of_lines],\
				'ymin':columns[4][level:level+no_of_lines],\
				'xmax':columns[5][level:level+no_of_lines],\
				'ymax':columns[6][level:level+no_of_lines]\
			}
		level = len(columns[0])
	elif (level+no_of_lines<=len(columns[0])):
		lines = {'image_name':columns[0][level:level+no_of_lines],\
				'CLASS_ID':columns[1][level:level+no_of_lines],\
				'confidence':columns[2][level:level+no_of_lines],\
				'xmin':columns[3][level:level+no_of_lines],\
				'ymin':columns[4][level:level+no_of_lines],\
				'xmax':columns[5][level:level+no_of_lines],\
				'ymax':columns[6][level:level+no_of_lines]\
			}
		level = level + no_of_lines

	return lines


#++++++++++++++++++++++++++++ read_csv: Internal Function ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This function simulates a recognition program. It should be replaced.  
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

#++++++++++++++++++++++++++++ simulate_score: Internal Function ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#
# This function simulates recognition of different scores.
#
# Functionality : 
# Corrupts the database: It changes the CLASS_ID field of a line randomly picked with probability (1 - score/100)
# 
# Usage: simulate_score(score)
# 
# Inputs: 
#         1. score: Score [0,100] which needs to be obtained.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def simulate_score (score):
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
    global temp_directory
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hw:p:", ["help", "ip=", "port=", "user=", "pass=", "in=", "im_dir=","temp_dir=","score="])
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
	elif switch == "--im_dir":
	    image_directory = val
	elif switch == "--temp_dir":
	    temp_directory = val
	elif switch in ("-s","--score"):
	    score = int(val)
        else:
            assert False, "unhandled option"

    print "\nhost = "+host_ipaddress+":"+host_port+"\nUsername = "+username+"\nPassword = "+password+"" 


#+++++++++++++++++++++++++++ Global Variables ++++++++++++++++++++++++++++++++++++++++++++++++++++
host_ipaddress = '128.46.75.108'
host_port = '80'
password = ''
score = 100
username = ''
csv_filename = 'golden_output.csv'
image_directory = '../images'
temp_directory = '../temp'

#+++++++++++++++++++++++++++ Start of the script +++++++++++++++++++++++++++++++++++++++++++++++
parse_cmd_line()
[token, status] = get_token(username,password)   # Login to server and obtain token
if status==0:
	print "Incorrect Username and Password. Bye!"
	sys.exit()
read_csv(csv_filename)                 # Read the csv file to obtain the data
simulate_score(score)                     # Corrupt the databaseread to obtain a score of 'score'
[no_of_images, status] = get_no_of_images(token)
if status==0:
	print "Token, Incorrect or Expired. Bye!"
	sys.exit()
# This is for illustration purpose
while 1==1:
	for w in range (1,int(no_of_images)+1,1):
		if get_image(token,w)==0:             # If get_image failed, exit.
			print "Get Image Failed, Exiting, Bye!"
			sys.exit()
		else:
			print "Image Stored in client directory "+image_directory+"/"+str(w)+".jpg"
                time.sleep(5)
		line = get_lines(1)
		if post_result(token,line)==0:        # If post_result failed, exit.
			print "Get Image Failed, Exiting, Bye!"
			sys.exit()

		print

