#!/usr/bin/env python
usage_text = """
LPIRC Referee Server 
====================
@2015 - HELPS, Purdue University

TO-DO:
1. Power meter reading
2. Exporting data from database to csv file for post processing



Rules:
1. If a single image has multiple bounding boxes, the client can send the bounding boxes in the same POST message.
2. The client may send multiple POST messages for different bounding boxes of the same image.
3. Two different images need to be sent in the different POST messages.
4. The POST messages for different images may be out of order.
   (for example, the bounding boxes for image 5 may be sent before the bounding boxes for image 3)


Main Tasks:
-----------
1. Authenticate user and provide time limited token for the session.
     - Timeout is set to 5 minutes by default. 
     - If multiple attempts are made to login, all the previous data will be overwritten.
2. Send images to token validated client devices upon GET request.
     - The image list in the local directory is refreshed every time before an image is sent.
     - This feature allows image directory to be modified with server running.
3. Receive asynchronous post results for final evaluation.
     - The results are stored in a database.
     - Database allows results to be stored for all users in a single file.
     - Only required user's data is written to a csv file for post processing
4. Get power meter readings from powermeter.
     - Powermeter readings are also stored in the same database.

Requirements:
-------------
1. Python v2.7.3
2. Flask v0.10.x - Microframework for Python
3. Flask-SQLAlchemy
4. Flask-Login          
5. itsdangerous v0.24   


Installation:
-------------
1. Install Python v2.7.3
2. Install any Python package manager (example pip)
      ref:https://pip.pypa.io/en/latest/installing.html
3. Install required packages
      a. Flask 
               pip install Flask
               ref: http://flask.pocoo.org/docs/0.10/installation/
      b. Flask-Login 
               pip install Flask-Login
      c. Flask-SQLAlchemy 
               pip install Flask-SQLAlchemy
               ref: https://github.com/mitsuhiko/flask-sqlalchemy
      d. itsdangerous 
               pip install itsdangerous
               ref: http://pythonhosted.org//itsdangerous/

4. Check referee.py for options 
      python referee.py --help
5. Host server 
      python referee.py --ip 127.0.0.1 --port 5000 --images "../images/*.jpg" --timeout 300
       - Hosts server at 127.0.0.1:5000, sending images (*.jpg) to client from directory "../images".
       - Session timeout of 300 seconds


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
                Default: images/*.jpg

         --result
                Test results (Relative to root directory)
                Default: result/result.csv

         --debug
                Run server in debug mode
                Default: debug = None

         --secret
                Secret key to generate token

         --timeout
                Client session timeout in seconds
                Default: 300 seconds (5 Minutes)

         -h, --help
                Displays all the available option


Following URLs are recognized, served and issued:
------------------------------------------------
Assumptions:
-----------
1. Image index starts from 1 (not 0).
2. Command line arguments expect to be within quotes
3. Use sql browser to view database (http://sqlitebrowser.org/)

"""
import getopt, sys, re, glob, os                                          # Parser for command-line options
from datetime import datetime,date,time                                   # Python datetime for session timeout
from flask import Flask, url_for, send_from_directory, request, Response  # Webserver Microframework
from flask.ext.login import LoginManager, UserMixin, login_required       # Login manager 
from itsdangerous import JSONWebSignatureSerializer                       # Token for authentication
from flask.ext.sqlalchemy import SQLAlchemy                               # lpirc session database


app = Flask(__name__)
# username-password
login_manager = LoginManager()
login_manager.init_app(app)
# session manager
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/lpirc.db'
db = SQLAlchemy(app)




#++++++++++++++++++++++++++++++++ Global Variables +++++++++++++++++++++++++++++++++++
host_ipaddress = '127.0.0.1'
host_port = '5000'
test_images_dir_wildcard = '../images/*.JPEG'
test_result = 'result/result.csv'
mode_debug = 'True' #'None'
server_secret_key = 'ITSASECRET'
timeout = 300 #seconds

#++++++++++++++++++++++++++++++++ URLs +++++++++++++++++++++++++++++++++++++++++++++++
url_root = '/'
url_help = '/help'
url_login = '/login'
url_get_token = '/get_token'
url_verify_token = '/verify'
url_get_image = '/image'
url_post_result = '/result'
url_no_of_images = '/no_of_images'

#++++++++++++++++++++++++++++++++ Macros/Form-Fields ++++++++++++++++++++++++++++++++++
ff_username = 'username'
ff_password = 'password'
ff_timestamp = 'timestamp'
ff_token = 'token'
ff_image_index = 'image_name'
ff_class_id = 'CLASS_ID'
ff_confidence = 'confidence'
ff_bb_xmin = 'xmin'
ff_bb_xmax = 'xmax'
ff_bb_ymin = 'ymin'
ff_bb_ymax = 'ymax'

datetime_format = "%d/%m/%yT%H:%M:%S.%f"

#++++++++++++++++++++++++++++++++ Help URL - Response ++++++++++++++++++++++++++++++++++
server_help_message = ("""
Valid URLs:
            (post/get)     --NA--                            host/
                                                             Example: curl 127.0.0.1:5000/

            (post/get)     --NA--                            host%s
                                                             Example: curl 127.0.0.1:5000%s

            (post)      (%s=[user]&%s=[pass])    host%s
                                                             Example: curl --data "%s=user&%s=pass" 127.0.0.1:5000%s

            (post)      (%s=[token])                      host%s
                                                             Example: curl --data "%s=daksldjsaldkjlkj32....." 127.0.0.1:5000%s

            (post)      (%s=[token]&%s=[image_index])  host%s (Image index starts with 1: 1,2,3,...)
                                                             Example: curl --data "%s=daks....&%s=3" 127.0.0.1:5000%s

            (post)      (%s=[token]&%s=[image_index]&..
                         %s=[id]&%s=[conf]&..
                         %s=[xmin]&%s=[xmax]&..
                         %s=[ymin]&%s=[ymax])            host%s
                                                             Example: curl --data "%s=daks....&%s=3&
                                                                                   %s=7&%s=0.38&
                                                                                   %s=123.00&%s=456.00&
                                                                                   %s=132.00&%s=756.00"     127.0.0.1:5000%s

""" %
    (url_help, url_help, 
     ff_username, ff_password, url_login, 
     ff_username, ff_password, url_login, 
     ff_token, url_verify_token, 
     ff_token, url_verify_token, 
     ff_token, ff_image_index, url_get_image, 
     ff_token, ff_image_index, url_get_image, 
     ff_token, ff_image_index, 
     ff_class_id, ff_confidence, 
     ff_bb_xmin, ff_bb_xmax, 
     ff_bb_ymin, ff_bb_ymax, url_post_result, 
     ff_token, ff_image_index, 
     ff_class_id, ff_confidence, 
     ff_bb_xmin, ff_bb_xmax, 
     ff_bb_ymin, ff_bb_ymax, url_post_result))


resp_login_fail = 'Invalid username or password\n'
resp_invalid_token = 'Invalid Token\n'
resp_valid_token = 'Valid Token\n'
resp_invalid_image_index = 'Invalid Image index\n'
resp_image_index_out_of_range = 'Image index out of range\n'
resp_image_dir_not_exist = 'Image directory does not exist\n'
resp_missing_result_field = 'Missing result field\n'
resp_result_stored = 'Result stored in the server database\n'
resp_result_length_mismatch = 'Result field length mismatch\n'
resp_missing_username_or_password = 'Missing username or password\n'

#++++++++++++++++++++++++++++++++ Username/Password Database ++++++++++++++++++++++++++
#
# Each team will be assigned a pair of username and passwords. 
#
# Minimal Flask-Login Example
# Ref: http://gouthamanbalaraman.com/minimal-flask-login-example.html
class User(UserMixin):
    # proxy for a database of users
    user_database = {"lpirc": ("lpirc", "pass"),
                     "user_330": ("user_330", "pass@#$2249")}
 
    def __init__(self, username, password):
        self.id = username
        self.password = password
 
    @classmethod
    def get(cls,id):
        return cls.user_database.get(id)


#++++++++++++++++++++++++++++++++ Session sqlalchemy Database ++++++++++++++++++++++++++
# Ref:
#      1. http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database
#      2. https://pythonhosted.org/Flask-SQLAlchemy/quickstart.html#simple-relationships

# Session database maintains the session information.
# A session is created or overwritten, each time an user logs in.
class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    timestamp = db.Column(db.DateTime)
    results = db.relationship('Result', backref='author', lazy='dynamic')

    def __init__(self, username, email, results=None, timestamp=None):
        self.username = username
        self.email = email
        if timestamp is None:
            timestamp = datetime.now()
        self.timestamp = timestamp
        if results is None:
            results = Result()
        self.results = [results]

    def __repr__(self):
        return '<Session %r>' % self.username


# Result database is associated with a session
class Result(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    image = db.Column(db.String(40))
    class_id = db.Column(db.String(40))
    confidence = db.Column(db.String(40))
    xmin = db.Column(db.String(40))
    xmax = db.Column(db.String(40))
    ymin = db.Column(db.String(40))
    ymax = db.Column(db.String(40))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('session.id'))


    def __repr__(self):
        return '<Result %r>' % (self.image)



#++++++++++++++++++++++++++++++++ Root url - Response +++++++++++++++++++++++++++++++++++
# Help and Default options
@app.route(url_root,methods=['post','get'])
@app.route(url_help,methods=['post','get'])
def server_help():
    return Response(response=server_help_message, status=200)


#++++++++++++++++++++++++++++++++ login url - Response +++++++++++++++++++++++++++++++++++
# Login function
@app.route(url_login, methods=['post','get'])
@app.route(url_get_token, methods=['post','get'])
def login_check():
    try:
    	rx_username = request.form[ff_username]
    	rx_password = request.form[ff_password]
    except:
	return Response(response=resp_missing_username_or_password, status=401) # Unauthorized
    # Validate username and password
    if verify_user_entry(rx_username,rx_password) is None:
        return Response(response=resp_login_fail, status=401) # Unauthorized
    else:
        # Generate time limited token
        token = generate_token(rx_username,rx_password)
        return Response(response=token, status=200)


#++++++++++++++++++++++++++++++++ Verify Token url - Response +++++++++++++++++++++++++++++
# Verify Token
@app.route(url_verify_token,methods=['post','get'])
def token_check():
    token = request.form[ff_token]
    if verify_user_token(token) is None:
        return Response(response=resp_invalid_token, status=401) # Unauthorized
    else:
        return Response(response=resp_valid_token, status=200)


#++++++++++++++++++++++++++++++++ Send Image url - Response ++++++++++++++++++++++++++++++++
# Send Images
@app.route(url_get_image,methods=['post','get'])
def send_image():
    token = request.form[ff_token]
    if verify_user_token(token) is None:
        return Response(response=resp_invalid_token, status=401)
    else:
	list_of_images = glob.glob(test_images_dir_wildcard)
        # Token Verified, Send back images
        image_index_str = request.form[ff_image_index]
        match = re.search("[^0-9]", image_index_str)
        if match:
            return Response(response=resp_invalid_image_index, status=406)  # Not Acceptable
        image_index = int(image_index_str)
        if (image_index <= 0) or (image_index > len(list_of_images)):
            return Response(response=resp_image_index_out_of_range, status=406) # Not Acceptable
        # Assuming image index starts with 1. example: 1,2,3,....
        image_index -= 1

        # List all images in directory
        list_of_images = glob.glob(test_images_dir_wildcard)
        # Flask send file expects split directory arguments
        split_path_image = os.path.split(list_of_images[image_index])
        return send_from_directory(split_path_image[0], split_path_image[1], as_attachment=True)        


#++++++++++++++++++++++++++++++++ Total number of images - Response ++++++++++++++++++++++++++++++++
# Send number of images
@app.route(url_no_of_images,methods=['post'])
def send_no_of_images():
    try:
    	token = request.form[ff_token]
    except:
	return Response(response=resp_invalid_token, status=401) # Unauthorize
    if verify_user_token(token) is None:
        return Response(response='Invalid User', status=401)  # Unauthorized
    else:
	total_number_images = len(glob.glob(test_images_dir_wildcard))
        return Response(response=str(total_number_images), status=200)



#++++++++++++++++++++++++++++++++ Log results url - Response ++++++++++++++++++++++++++++++++
# Store result
@app.route(url_post_result, methods=['post'])
def store_result():
    token = request.form[ff_token]
    if verify_user_token(token) is None:
        return Response(response=resp_invalid_token, status=401)
    else:
        # Read result fields
        try:
            t_image_name = request.form.getlist(ff_image_index)
            t_class_id = request.form.getlist(ff_class_id)
            t_confidence = request.form.getlist(ff_confidence)
            t_xmin = request.form.getlist(ff_bb_xmin)
            t_ymin = request.form.getlist(ff_bb_ymin)
            t_xmax = request.form.getlist(ff_bb_xmax)
            t_ymax = request.form.getlist(ff_bb_ymax)
        except:
            return Response(response=resp_missing_result_field, status=406)

        # Update result database
        t_user = get_username(token)
        sess = Session.query.filter_by(username=t_user).first()
        t_count = len(t_image_name)
        try:
            for k in range(0,t_count):
                t_res = Result(image=t_image_name[k], class_id=t_class_id[k], \
                               confidence=t_confidence[k], \
                               xmin=t_xmin[k], xmax=t_xmax[k], \
                               ymin=t_ymin[k], ymax=t_ymax[k], \
                               timestamp=datetime.utcnow(), \
                               author=sess)
                db.session.add(t_res)

            db.session.commit()
            return Response(response=resp_result_stored, status=200)

        except:
            return Response(response=resp_result_length_mismatch, status=406)



	# if len(image_name)==len(CLASS_ID)==len(confidence)==len(xmin)==len(ymin)==len(xmax)==len(ymax)>0:
	# 	s=""
	# 	for item in range(0,len(ymax)):
	# 		s=s+(image_name[item] + "," + CLASS_ID[item] + "," + confidence[item] + "," + xmin[item] + "," + ymin[item] + "," + xmax[item] + "," + ymax[item] + "\n")
	# 		with open('./out.csv','a') as fout:
	# 			fout.write(s)	
	# 			fout.close()	
     	# 	return "Result Stored\n"
	# else:
	# 	print("Incorrect lines\n")
	# 	return "Incorrect Lines\n"


#++++++++++++++++++++++++++++++++ Internal Functions +++++++++++++++++++++++++++++++++++
# Verify user credentials
def verify_user_entry(a_username,a_password):
    user_entry = User.get(a_username)
    if (user_entry is not None):
        user = User(user_entry[0],user_entry[1])
        if (user.password == a_password):
            return "Valid"
        else:
            return None

    return None

def get_credential(a_token):
    s = JSONWebSignatureSerializer(server_secret_key)
    try:
        credential = s.loads(a_token)
        return credential
    except:
        return None


def get_username(a_token):
    credential = get_credential(a_token)
    if credential is None:
        return None

    return credential[ff_username]


def verify_user_token(a_token):
    credential = get_credential(a_token)
    if credential is None:
        return None

    if verify_user_entry(credential[ff_username],credential[ff_password]) is None:
        return None
    else:
        # Verify if timeout
        dt = datetime.strptime(credential[ff_timestamp], datetime_format)
        elapsed = datetime.now()-dt
        if elapsed.total_seconds() > timeout:
            print "Elapsed Time = {}".format(elapsed.total_seconds())
            return None
        else:
            return "Valid"
    

# Generate time stamped token
def generate_token(a_username,a_password):
    if valid_lpirc_session(a_username) is None:
        create_lpirc_session(a_username)
    else:
        # Should be a penalty for multiple login attempts
        delete_lpirc_session(a_username)
        create_lpirc_session(a_username)

    sess = Session.query.filter_by(username=a_username).first()
    s = JSONWebSignatureSerializer(server_secret_key)
    dt = sess.timestamp
    dt_str = dt.strftime(datetime_format)
    print dt_str
    # Adding session created time for timeout validation
    token = s.dumps({ff_username: a_username, ff_password: a_password, ff_timestamp: dt_str})
    return token

# Check if lpirc session exists in database
def valid_lpirc_session(a_username):
    if Session.query.filter(Session.username == a_username).first() is None:
        return None
    else:
        return "valid"



# Create a session entry in lpirc database
def create_lpirc_session(a_username):
    # Check if a session for the user already exists
    if Session.query.filter(Session.username == a_username).first() is None:
        s = Session(a_username,None)
        db.session.add(s)
        db.session.commit()
        print "LPIRC session created for {}\n".format(a_username)
    else:
        print "LPIRC session already exists for {}\n".format(a_username)
        
    return

# Delete session entry in lpirc database
def delete_lpirc_session(a_username):
    # Query session related to user
    s = Session.query.filter(Session.username == a_username).first()
    if s is None:    # No session entry exists
        print "No lpirc session exists for {}\n".format(a_username)
    else:
        db.session.delete(s)
        db.session.commit()
        print "lpirc session deleted for {}\n".format(a_username)

    return


# Script usage function
def usage():
    print usage_text

# Initialize global variables
def init_global_vars():

    global test_images_dir_wildcard   # eg ../../data/images/*.jpg

    image_wildcard = os.path.basename(test_images_dir_wildcard)
    image_dirname = os.path.dirname(test_images_dir_wildcard)

    # Check if basename contains wildcard
    if re.search('[\*\.]', image_wildcard) == None:     # Still Folder name or empty
        assert os.path.exists(test_images_dir_wildcard), test_images_dir_wildcard+'--'+resp_image_dir_not_exist
        test_images_dir_wildcard = os.path.join(test_images_dir_wildcard, '*.*')
        
    total_number_images = len(glob.glob(test_images_dir_wildcard))
    print "Found %d test images in %s \n" % (total_number_images, test_images_dir_wildcard)
    return



#++++++++++++++++++++++++++++++++ Parse Command-line Input +++++++++++++++++++++++++++++++
# Main function to parse command-line input and run server
def parse_cmd_line():

    global host_ipaddress
    global host_port
    global test_images_dir_wildcard
    global test_result
    global mode_debug
    global server_secret_key
    global timeout

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hw:p:", ["help", "ip=", "port=", "images=", "result=", "debug", "secret=", "timeout="])
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
            test_images_dir_wildcard = val
        elif switch == "--result":
            test_result = val
        elif switch == "--debug":
            mode_debug = 'True'
        elif switch == "--secret":
            server_secret_key = val
        elif switch == "--timeout":
            timeout = int(val)
        else:
            assert False, "unhandled option"

    print "\nhost = "+host_ipaddress+":"+host_port+"\nTest Images = "+test_images_dir_wildcard+"\nTest Result = "+test_result+"\nDebug Mode  = "+mode_debug+"\nTimeout  = "+str(timeout)+"\n" 




#++++++++++++++++++++++++++++++++ Script enters here at beginning +++++++++++++++++++++++++++++++++++
if __name__ == "__main__":
    # Parse Command-line
    parse_cmd_line()
    # Initialize global variables
    init_global_vars()
    # Initialize lpirc session database
    db.create_all()
    # Start server
    app.config["SECRET_KEY"] = server_secret_key
    app.run(host=host_ipaddress, port=int(host_port), debug=mode_debug)


