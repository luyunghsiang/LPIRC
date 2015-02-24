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

         -h, --help
                Displays all the available option


"""


import pycurl
import getopt,sys
try:
    # python 3
    from urllib.parse import urlencode
except ImportError:
    # python 2
    from urllib import urlencode

from StringIO import StringIO as BytesIO
from StringIO import StringIO

def get_image(token, number):
	c = pycurl.Curl()
	c.setopt(c.URL, host_ipaddress+':'+host_port+'/image/?image='+str(number))
	post_data = {'token':token}
	postfields = urlencode(post_data)
	c.setopt(c.POSTFIELDS,postfields)
	with open('image'+str(number)+'.jpg', 'w') as f:
    		c.setopt(c.WRITEDATA, f)
    		c.perform()
    		c.close()

def post_result(token, data):
	c = pycurl.Curl()
	c.setopt(c.URL, host_ipaddress+':'+host_port+'/result')
	post_data = {'token':token}
	postfields = urlencode(post_data)+'&'+urlencode(data,True)
	print postfields
	c.setopt(c.POSTFIELDS,postfields)
   	c.perform()
    	c.close()

# Script usage function
def usage():
    print usage_text

# Main function to parse command-line input and run server
def parse_cmd_line():

    global host_ipaddress
    global host_port
    global username
    global password

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hw:p:", ["help", "ip=", "port=", "user=", "pass="])
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
        else:
            assert False, "unhandled option"

    print "\nhost = "+host_ipaddress+":"+host_port+"\nUsername = "+username+"\nPassword = "+password+"" 


# Parse Command-line
host_ipaddress = '127.0.0.1'
host_port = '5000'
password = 'pass'
username = 'lpirc'
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
print(token)



get_image(token,1)
data = {'image_name':'picasa','CLASS_ID':'12','confidence':'0.3','xmin':'100','ymin':'10','xmax':'500','ymax':'200'}
post_result(token,data)

	
		
