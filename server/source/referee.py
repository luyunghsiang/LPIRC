usage_text = """
LPIRC Referee Server 
====================
@2015 - HELPS, Purdue University

Main Tasks:
-----------
1. Authenticate user and provide time limited token for the session.
2. Send images to token validated client devices upon GET request.
3. Receive asynchronous post results for final evaluation.
4. Get power meter readings from powermeter.

Requirements:
-------------
1. Python v2.7.3
2. Flask - Microframework for Python

Usage:
------
referee.py [OPTION]...
Options:
         -w, --ip
                IP address of the server in format <xxx.xxx.xxx.xxx>
                Default: 127.0.0.1

         -p, --port
                Port number of the server.
                Default: 5000

         --images
                Test images (Relative to root directory)
                Default: images/*.png

         --result
                Test results Directory (Relative to root directory)
		The results of user John is stored as /result/John.csv
                Default: result

         --debug
                Run server in debug mode
                Default: debug = None

         -h, --help
                Displays all the available option


Following URLs are recognized, served and issued:


"""
from random import randint
import cgi
import getopt, sys                                                        # Parser for command-line options
from flask import Flask, url_for, send_from_directory, request, Response  # Webserver Microframework
from flask.ext.login import LoginManager, UserMixin, login_required       # Login manager 
from itsdangerous import JSONWebSignatureSerializer                       # Token for authentication


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)



# Global Variables
host_ipaddress = '127.0.0.1'
host_port = '5000'
test_images = 'images'
test_result = 'result'
mode_debug = 'True' #'None'
server_secret_key = 'ITSASECRET'
result_file = 'result'
sent_image_dictionary =[]

# Minimal Flask-Login Example
# Ref: http://gouthamanbalaraman.com/minimal-flask-login-example.html
class User(UserMixin):
    # proxy for a database of users
    user_database = {"lpirc": ("lpirc", "pass"),
                     "JaneDoe": ("JaneDoe", "Jane"),
                     "user": ("user", "pass"),
                     "JaneDoe": ("JaneDoe", "Jane")}
 
    def __init__(self, username, password):
        self.id = username
        self.password = password
 
    @classmethod
    def get(cls,id):
        return cls.user_database.get(id)


# Help and Default options
@app.route("/",methods=['post','get'])
@app.route("/help",methods=['post','get'])
def server_help():
    server_help_message = """
    Valid URLs:
        host/
        host/help
        (Post) host/login [username&password] example: username=user&password=pass
        (Post) host/verify [token] example: token=daksldjsaldkjlkj32.....
        (get/Post) host/image/?image=[#Image]  [token]  example: token=lsadkjsldj... host/image/?image=10
        (Post) host/result [token&image_name&CLASS_ID&confidence&xmin&xmax&ymin&ymax&...]  example: token=daksldjsaldkjlkj32.....&image_name=picase&CLASS_ID=2&confidence=.3&xmin=123&ymin=132&xmax=456&ymax=450... [note: n complete lines can be added in single post. To make n entries, 7n+1 form values]

    """
    return Response(response=server_help_message, status=200)


# Login function
@app.route('/login', methods=['post','get'])
@app.route('/get_token', methods=['post','get'])
def login_check():
    global result_file
    global sent_image_dictionary
    sent_image_dictionary	 = []
    rx_username = request.form['username']
    rx_password = request.form['password']
    # Validate username and password
    if verify_user_entry(rx_username,rx_password) is None:
        return Response(response='Incorrect username or password', status=200)
    else:
	result_file = rx_username
        # Generate Token
        s = JSONWebSignatureSerializer(server_secret_key)
        token = s.dumps({'username': rx_username, 'password' : rx_password})
        return Response(response=token, status=200)


# Verify Token
@app.route("/verify",methods=['post','get'])
def token_check():
    token = request.form['token']
    if verify_user_token(token) is None:
        return Response(response='Invalid', status=200)
    else:
        return Response(response='Valid', status=200)


# Send Images
@app.route("/image/",methods=['post','get'])
def send_image():
    global test_images
    global sent_image_dictionary
    token = request.form['token']
    if verify_user_token(token) is None:
        return Response(response='Invalid User', status=200)
    else:
        # Token Verified, Send back images
        image_number = request.args.get('image')
	sent_already = [item for item in sent_image_dictionary if item[0] == int(image_number)]
	if not sent_already:
		image_chosen = randint(3*(int(image_number)-1),2+(3*(int(image_number)-1)))
		sent_image_dictionary.append((int(image_number),int(image_chosen)))
        #	print "#Image = "+str(image_number)+"      "+str(image_chosen)
	else:
		image_chosen = sent_already[0][1]
	#	print "#Image = "+str(image_number)+"      "+str(image_chosen)
#	print sent_image_dictionary
        return send_from_directory('./../'+test_images,str(image_chosen)+'.jpg',as_attachment=True)


# Store result
@app.route("/result",methods=['post'])
def store_result():
    global result_file
    global sent_image_dictionary
    token = request.form['token']
    if verify_user_token(token) is None:
        return Response(response='Invalid User', status=200)
    else:
        # Token Verified, Send back images
       	form = cgi.FieldStorage()
	image_name = request.form.getlist("image_name")
	CLASS_ID = request.form.getlist("CLASS_ID")
	confidence = request.form.getlist("confidence")
	xmin = request.form.getlist("xmin")
	ymin = request.form.getlist("ymin")
	xmax = request.form.getlist("xmax")
	ymax = request.form.getlist("ymax")
	if len(image_name)==len(CLASS_ID)==len(confidence)==len(xmin)==len(ymin)==len(xmax)==len(ymax)>0:
		s=""
		for item in range(0,len(ymax)):
			p=dict(sent_image_dictionary)[int(image_name[item])]	
			s=s+(str(p) + " " + CLASS_ID[item] + " " + confidence[item] + " " + xmin[item] + " " + ymin[item] + " " + xmax[item] + " " + ymax[item] + "\n")
		with open('../../'+test_result+'/'+result_file+'.csv','a') as fout:
			fout.write(s)	
			fout.close()	
     		return "Result Stored in ../../"+test_result+"/"+result_file+".csv\n"
	else:
		print("Incorrect lines\n")
		return "Incorrect Lines\n"


# Verify user credentials
def verify_user_entry(a_username,a_password):
    user_entry = User.get(a_username)
    #result_file = a_username
    if (user_entry is not None):
        user = User(user_entry[0],user_entry[1])
        if (user.password == a_password):
            return "Valid"
        else:
            return None

    return None

def verify_user_token(a_token):
    s = JSONWebSignatureSerializer(server_secret_key)
    credential = s.loads(a_token)
    if verify_user_entry(credential['username'],credential['password']) is None:
        return None
    else:
        return "Valid"

# Script usage function
def usage():
    print usage_text

# Main function to parse command-line input and run server
def parse_cmd_line():

    global host_ipaddress
    global host_port
    global test_images
    global test_result
    global mode_debug
    global server_secret_key

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hw:p:", ["help", "ip=", "port=", "images=", "result=", "debug", "secret="])
    except getopt.GetoptError as err:
        # print help information and exit:
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
        elif switch == "--images":
            test_images = val
        elif switch == "--result":
            test_result = val
        elif switch == "--debug":
            mode_debug = 'True'
        elif switch == "--secret":
            server_secret_key = val
        else:
            assert False, "unhandled option"

    print "\nhost = "+host_ipaddress+":"+host_port+"\nTest Images = "+test_images+"\nTest Result = "+test_result+"\nDebug Mode  = "+mode_debug 


if __name__ == "__main__":
    # Parse Command-line
    parse_cmd_line()
    # Start server
    app.config["SECRET_KEY"] = server_secret_key
    app.run(host=host_ipaddress, port=int(host_port), debug=mode_debug)
