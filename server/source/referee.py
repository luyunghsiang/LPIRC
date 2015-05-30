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
                Default: ../images/*.jpg

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

         --enable_powermeter
                Enables powermeter

         -h, --help
                Displays all the available option


Following URLs are recognized, served and issued:
------------------------------------------------
Note:
-----
1. Image index starts from 1 (not 0).
2. Command line arguments expect to be within quotes
3. Use sql browser to view database (http://sqlitebrowser.org/)

"""
import getopt, sys, re, glob, os                                          # Parser for command-line options
from datetime import datetime,date,time                                   # Python datetime for session timeout
from flask import Flask, url_for, send_from_directory, request, Response  # Webserver Microframework
from flask import redirect                                                # Flask modules
from flask.ext.login import LoginManager, UserMixin, login_required       # Login manager 
from itsdangerous import JSONWebSignatureSerializer                       # Token for authentication
from flask.ext.sqlalchemy import SQLAlchemy                               # lpirc session database
import shlex                                                              # For constructing popen shell arguments
import subprocess                                                         # Non-blocking program execution (Popen, PIPE)
import time                                                               # For sleep
import string, random
import csv                                                                # Export database entries for scoring


#++++++++++++++++++++++++++++++++ Global Variables +++++++++++++++++++++++++++++++++++
this_file_path = os.path.dirname(os.path.abspath(__file__))

host_ipaddress = '127.0.0.1'
host_port = '5000'
test_images_dir_wildcard = os.path.join(this_file_path, '../images/*.*')
test_result = os.path.join(this_file_path, 'result/result.csv')
mode_debug = 'None' #'None'
server_secret_key = 'ITSASECRET'
timeout = 300 #seconds
lpirc_db = os.path.join(this_file_path, '../database/lpirc.db')

enable_powermeter = 0
powermeter_client = os.path.join(this_file_path, '../powermeter/wt310_client.py')
powermeter_ipaddress = '192.168.1.3'
powermeter_update_interval = 1 # seconds
powermeter_mode = 'RMS' # DC | RMS

lpirc_powercsv_dir = os.path.join(this_file_path, '../csv/powermeter/')
lpirc_resultcsv_dir = os.path.join(this_file_path, '../csv/submissions/')
#++++++++++++++++++++++++++++++++ URLs +++++++++++++++++++++++++++++++++++++++++++++++
url_root = '/'
url_help = '/help'
url_login = '/login'
url_get_token = '/get_token'
url_verify_token = '/verify'
url_get_image = '/image'
url_post_result = '/result'
url_no_of_images = '/no_of_images'
url_logout = '/logout'
url_post_powermeter_readings = '/powermeter'
url_csvsave_submissions = '/savecsv'
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
ff_player = 'player'
ff_voltage = 'voltage'
ff_current = 'current'
ff_power = 'power'
ff_energy = 'energy'
ff_elapsed = 'elapsed'

session_status_active = 'session_active'
session_status_inactive = 'session_inactive'
session_status_idle = 'session_idle'
session_status_timeout = 'session_timeout'
session_status_lock = 'session_locked'

datetime_format = "%d/%m/%yT%H:%M:%S.%f"

#++++++++++++++++++++++++++++++++ Powermeter Macros ++++++++++++++++++++++++++++++++++
powermeter_user = 'wt310'
powermeter_password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))

pmc_cmd_ipaddress = '--pmip'
pmc_cmd_update_interval = '--pminterval'
pmc_cmd_mode = '--pmmode'
pmc_cmd_timeout = '--pmtimeout'
pmc_cmd_ping = '--pm_ping'
pmc_cmd_hard_reset = '--pm_hard_reset'
pmc_cmd_soft_reset = '--pm_soft_reset'
pmc_cmd_user = '--pmuser'
pmc_cmd_password = '--pmpassword'
pmc_cmd_player = '--pmplayer'
pmc_cmd_start = '--pm_start'
pmc_cmd_stop = '--pm_stop'
pmc_cmd_host_ip = '--host_ip'
pmc_cmd_host_port = '--host_port'

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

            (post)      (%s=[token]&%s=[player_name]&..
                         %s=[voltage]&%s=[current]&..
                         %s=[power]&%s=[energy]&..
                         %s=[elapsed_time])            host%s
                                                             Example: curl --data "%s=daks....&%s=lpirc&
                                                                                   %s=120&%s=0.1&
                                                                                   %s=9&%s=45&
                                                                                   %s=5"     127.0.0.1:5000%s

            (post)      (%s=[token]&%s=[player_name])  host%s (All submissions saved if no player_name)
                                                             Example: curl --data "%s=daks....&%s=lpirc" 127.0.0.1:5000%s


""" %
    (url_help, url_help, 
     ff_username, ff_password, url_login, 
     ff_username, ff_password, url_login, 
     ff_token, url_verify_token, 
     ff_token, url_verify_token, 
     ff_token, url_logout, 
     ff_token, url_logout, 
     ff_token, ff_image_index, url_get_image, 
     ff_token, ff_image_index, url_get_image, 
     ff_token, ff_image_index, 
     ff_class_id, ff_confidence, 
     ff_bb_xmin, ff_bb_xmax, 
     ff_bb_ymin, ff_bb_ymax, url_post_result, 
     ff_token, ff_image_index, 
     ff_class_id, ff_confidence, 
     ff_bb_xmin, ff_bb_xmax, 
     ff_bb_ymin, ff_bb_ymax, url_post_result,
     ff_token, ff_player, 
     ff_voltage, ff_current, 
     ff_power, ff_energy, 
     ff_elapsed, url_post_powermeter_readings, 
     ff_token, ff_player, 
     ff_voltage, ff_current, 
     ff_power, ff_energy, 
     ff_elapsed, url_post_powermeter_readings,
     ff_token, ff_player, url_csvsave_submissions,
     ff_token, ff_player, url_csvsave_submissions))


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
resp_logout = 'Logout success\n'
resp_powermeter_fail = 'Powermeter not connected\n'
resp_missing_powermeter_field = 'Missing powermeter field\n'
resp_power_readings_stored = 'Readings stored in the server database\n'
resp_power_readings_length_mismatch = 'Power readings field length mismatch\n'
resp_csvsave_success = 'Submissions stored in csv file\n'
resp_csvsave_fail = 'Error storing submissions in csv file\n'

#++++++++++++++++++++++++++++++++ Start Flask and Database ++++++++++++++++++++++++++
app = Flask(__name__)
# username-password
login_manager = LoginManager()
login_manager.init_app(app)
# session manager
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+lpirc_db
db = SQLAlchemy(app)



#++++++++++++++++++++++++++++++++ Username/Password Database ++++++++++++++++++++++++++
#
# Each team will be assigned a pair of username and passwords. 
#
# Minimal Flask-Login Example
# Ref: http://gouthamanbalaraman.com/minimal-flask-login-example.html
class User(UserMixin):
    # proxy for a database of users
    user_database = {"lpirc": ("lpirc", "pass"),
                     "user_330": ("user_330", "pass@#2249"),
                     # Powermeter User
                     powermeter_user: (powermeter_user, powermeter_password)}
 
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
    status = db.Column(db.String(120))
    results = db.relationship('Result', backref='author', lazy='dynamic')
    powermeter_readings = db.relationship('Powermeter', backref='author', lazy='dynamic')

    def __init__(self, username, email, results=None, timestamp=None, \
                 status=None, powermeter_readings=None):
        self.username = username
        self.email = email

        if status is None:
            status = session_status_active
        self.status = status

        if timestamp is None:
            timestamp = datetime.now()
        self.timestamp = timestamp

        if results is None:
            results = Result()
        self.results = [results]

        if powermeter_readings is None:
            powermeter_readings = Powermeter()
        self.powermeter_readings = [powermeter_readings]

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


# Powermeter database is associated with a session
class Powermeter(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    voltage = db.Column(db.String(40))
    current = db.Column(db.String(40))
    active_power = db.Column(db.String(40))
    accumulated_energy = db.Column(db.String(40))
    elapsed_time = db.Column(db.String(40))
    user_id = db.Column(db.Integer, db.ForeignKey('session.id'))

    def __repr__(self):
        return '<Powermeter %r>' % (self.elapsed_time)


#++++++++++++++++++++++++++++++++ Root url - Response +++++++++++++++++++++++++++++++++++
# Redirect to http://lpirc.net/
@app.route(url_root,methods=['post','get'])
def server_root_redirect():
    return redirect("http://lpirc.net/", code=302)



#++++++++++++++++++++++++++++++++ Help url - Response +++++++++++++++++++++++++++++++++++
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

    try:
        # Validate username and password
        if verify_user_entry(rx_username,rx_password) is None:
            return Response(response=resp_login_fail, status=401) # Unauthorized
        # Start Powermeter
        if ((enable_powermeter == 1) and (powermeter_start(rx_username) is not None)):
            return Response(response=resp_powermeter_fail, status=500)
        # Generate time limited token
        token = generate_token(rx_username,rx_password)
        return Response(response=token, status=200)
    except:
	return Response(response=resp_login_fail, status=500) # Internal


#++++++++++++++++++++++++++++++++ Logout - Response +++++++++++++++++++++++++++++
# Logout function
@app.route(url_logout, methods=['post','get'])
def logout_session():
    try:
    	token = request.form[ff_token]
    except:
	return Response(response=resp_invalid_token, status=401) # Unauthorize

    if verify_user_token(token) is None:
        return Response(response=resp_invalid_token, status=401) # Unauthorized
    else:
        credential = get_credential(token)
        set_session_status(credential[ff_username], session_status_inactive)
        return Response(response=resp_logout, status=200)


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

#++++++++++++++++++++++++++++++++ Submissions saveas csv file++++++++++++++++++++++++++++
@app.route(url_csvsave_submissions, methods=['post'])
def saveas_csvfile():
    token = request.form[ff_token]
    if get_username(token) != powermeter_user:
        return Response(response=resp_invalid_token, status=401)
    elif verify_user_token(token) is None:
        return Response(response=resp_invalid_token, status=401)
    else:
        # Get player name
        try:
            t_player = request.form.getlist(ff_player)
            this_player = t_player[0]
            write_csvfiles(this_player)
            return Response(response=resp_csvsave_success, status=200)
        except:
            return Response(response=resp_csvsave_fail, status=406)

        

#++++++++++++++++++++++++++++++++ Log Powermeter readings++++++++++++++++++++++++++++++++
@app.route(url_post_powermeter_readings, methods=['post'])
def store_powermeter_readings():
    token = request.form[ff_token]
    if get_username(token) != powermeter_user:
        return Response(response=resp_invalid_token, status=401)
    elif verify_user_token(token) is None:
        return Response(response=resp_invalid_token, status=401)
    else:
        # Read powermeter readings
        try:
            t_player = request.form.getlist(ff_player)
            t_voltage = request.form.getlist(ff_voltage)
            t_current = request.form.getlist(ff_current)
            t_power = request.form.getlist(ff_power)
            t_energy = request.form.getlist(ff_energy)
            t_elapsed = request.form.getlist(ff_elapsed)
        except:
            return Response(response=resp_missing_powermeter_field, status=406)

        # Update powermeter database
        this_player = t_player[0]
        sess = Session.query.filter_by(username=this_player).first()
        t_count = len(t_player)
        try:
            for k in range(0,t_count):
                if t_player[k] != this_player:
                    return Response(response=resp_power_readings_length_mismatch, status=406)
                    
                t_pmr = Powermeter(voltage = t_voltage[k], current = t_current[k], \
                                   active_power = t_power[k], accumulated_energy = t_energy[k], \
                                   elapsed_time = t_elapsed[k], author=sess)
                db.session.add(t_pmr)

            db.session.commit()
            return Response(response=resp_power_readings_stored, status=200)

        except:
            return Response(response=resp_power_readings_length_mismatch, status=406)



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
    elif get_session_status(credential[ff_username]) != session_status_active:
        print "Session not active: {}\n".format(get_session_status(credential[ff_username]))
        return None
    else:
        # Verify if timeout
        dt = datetime.strptime(credential[ff_timestamp], datetime_format)
        elapsed = datetime.now()-dt
        if elapsed.total_seconds() > timeout:
            # Set session status - Timeout
            set_session_status(credential[ff_username], session_status_timeout)
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

# Set session status -> active, inactive, idle, timeout
def set_session_status(a_username, a_status):
    sess = Session.query.filter_by(username=a_username).first()
    sess.status = a_status
    db.session.commit()
    return

# Get session status
def get_session_status(a_username):
    sess = Session.query.filter_by(username=a_username).first()
    return sess.status

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
        r_db = Result.query.filter(Result.user_id == s.id).delete()
        pm_db = Powermeter.query.filter(Powermeter.user_id == s.id).delete()
        db.session.delete(s)
        # db.session.delete(r_db)
        # db.session.delete(pm_db)
        db.session.commit()
        print "lpirc session deleted for {}\n".format(a_username)

    return


#++++++++++++++++++++++++++++++++ Powermeter Functions +++++++++++++++++++++++++++++++++++
# Powermeter client command line argument (Default)
def get_pmc_default_arg():
    default_command_line = "python\t" + powermeter_client + "\t" + \
                           pmc_cmd_ipaddress + "\t" + powermeter_ipaddress + "\t" + \
                           pmc_cmd_mode + "\t" + powermeter_mode + "\t" + \
                           pmc_cmd_timeout + "\t" + str(timeout) + "\t" + \
                           pmc_cmd_update_interval + "\t" + str(powermeter_update_interval)\

    return default_command_line

# Powermeter ping
def powermeter_ping():
    pm_command_line = get_pmc_default_arg()
    pm_command_line += "\t" + pmc_cmd_ping

    # Perform system call
    t_out = system_popen_execute(pm_command_line, "wait for it")
    if t_out is not None:
        print "Powermeter ping failed\n"
        return "Error"

    return None

# Powermeter start
def powermeter_start(t_player):
    if t_player == powermeter_user:
        return None

    if powermeter_ping() is not None:
        print "Powermeter communication error\n"
        return "Error"

    if powermeter_soft_reset() is not None:
        return "Error"

    pm_command_line = get_pmc_default_arg()
    # http client related
    pm_command_line += "\t" + pmc_cmd_host_ip + "\t" + host_ipaddress
    pm_command_line += "\t" + pmc_cmd_host_port + "\t" + host_port
    pm_command_line += "\t" + pmc_cmd_user + "\t" + powermeter_user
    pm_command_line += "\t" + pmc_cmd_password + "\t" + powermeter_password
    pm_command_line += "\t" + pmc_cmd_player + "\t" + t_player
    pm_command_line += "\t" + pmc_cmd_start
    # Perform system call
    t_out = system_popen_execute(pm_command_line)
    if t_out is not None:
        print "Powermeter start failed\n"
        return "Error"

    return None

# Powermeter soft reset
def powermeter_soft_reset():
    if powermeter_ping() is not None:
        print "Powermeter communication error\n"
        return "Error"

    pm_command_line = get_pmc_default_arg()
    pm_command_line += "\t" + pmc_cmd_soft_reset
    # Perform system call
    t_out = system_popen_execute(pm_command_line, "wait for it")
    if t_out is not None:
        print "Powermeter soft reset failed\n"
        return "Error"

    return None

# Powermeter hard reset
def powermeter_hard_reset():
    if powermeter_ping() is not None:
        print "Powermeter communication error\n"
        return "Error"

    pm_command_line = get_pmc_default_arg()
    pm_command_line += "\t" + pmc_cmd_hard_reset
    # Perform system call
    t_out = system_popen_execute(pm_command_line, "wait for it")
    if t_out is not None:
        print "Powermeter hard reset failed\n"
        return "Error"

    return None


    

# System Popen call
def system_popen_execute(a_args, a_wait_for_it=None):
    
    if sys.platform == 'win32':
        my_args = a_args.split()
    else:
        my_args = shlex.split(a_args)

    # Execute command
    print my_args
    try:
        p = subprocess.Popen(my_args, stdin = None, stdout = subprocess.PIPE, \
                             stderr = subprocess.PIPE, shell = False)
    except:
        print "Popen execution error\n"
        return "Error" # sys.exit(2) # Abnormal termination

    if a_wait_for_it is None:
        return None

    output = p.communicate()[0]

    if p.returncode != 0:
        print "Abnormal exit\n"
        return "Error" # sys.exit(2) # Abnormal termination

    return None


#++++++++++++++++++++++++++++++++++++ CSV Related ++++++++++++++++++++++++++++++++++
def write_csvfiles(this_player=None):
    # saveas player_name.csv
    player_list = []
    if not this_player:
        all_sess = Session.query.filter(Session.username != powermeter_user).all()
        for sess in all_sess:
            player_list.append(sess.username)
        print "Saving all submissions and powermeter readings\n"
    else:
        player_list.append(this_player)
        print "Saving csv file for player:{}".format(this_player)

    # Delete all empty entries
    rdb = Result.query.filter(Result.xmin == None).delete()
    pdb = Powermeter.query.filter(Powermeter.voltage == None).delete()
    db.session.commit()
    
    # Saving submissions and powermeter readings
    for player in player_list:
        all_result_rows = []
        all_power_rows = []
        
        mysess = Session.query.filter_by(username = player).first()
        myresults = Result.query.filter_by(author = mysess).all()
        for eachresult in myresults:
            each_result_row = [eachresult.image, \
                               eachresult.class_id, \
                               eachresult.confidence, \
                               eachresult.xmin, \
                               eachresult.ymin, \
                               eachresult.xmax, \
                               eachresult.ymax]
            all_result_rows.append(each_result_row)
            
        mypowers = Powermeter.query.filter_by(author = mysess).all()
        for eachpower in mypowers:
            each_power_row = [eachpower.voltage, \
                              eachpower.current, \
                              eachpower.active_power, \
                              eachpower.accumulated_energy, \
                              eachpower.elapsed_time]
            all_power_rows.append(each_power_row)
            
        mycsv = player + ".csv"
        resultcsvfile = os.path.join(lpirc_resultcsv_dir, mycsv)
        powercsvfile = os.path.join(lpirc_powercsv_dir, mycsv)
        
        with open(resultcsvfile, 'wb') as fid:
            writer = csv.writer(fid)
            writer.writerows(all_result_rows)

        with open(powercsvfile, 'wb') as fid:
            writer = csv.writer(fid)
            writer.writerows(all_power_rows)

    
    return "Success"



#------------------------- Input Parsing ---------------------------------    

# Script usage function
def usage():
    print usage_text

# Initialize global variables
def init_global_vars():

    global test_images_dir_wildcard   # eg ../../data/images/*.jpg
    test_images_dir_wildcard = os.path.join(this_file_path, test_images_dir_wildcard)

    global test_result
    test_result = os.path.join(this_file_path, test_result)

    image_wildcard = os.path.basename(test_images_dir_wildcard)
    image_dirname = os.path.dirname(test_images_dir_wildcard)

    print os.getcwd()+"\n"
    print os.path.dirname(os.path.abspath(__file__))+"\n"

    # Check if basename contains wildcard
    if re.search('[\*\.]', image_wildcard) == None:     # Still Folder name or empty
        assert os.path.exists(test_images_dir_wildcard), test_images_dir_wildcard+'--'+resp_image_dir_not_exist
        test_images_dir_wildcard = os.path.join(test_images_dir_wildcard, '*.*')
        
    total_number_images = len(glob.glob(test_images_dir_wildcard))
    print "Found %d test images in %s \n" % (total_number_images, test_images_dir_wildcard)

    # Check if windows for powermeter
    if (enable_powermeter == 1) and (sys.platform != 'win32'):
        print "Powermeter requires Windows environment\n"
        sys.exit(2)

    # # Reset powermeter
    # if (enable_powermeter == 1) and (powermeter_soft_reset() is not None):
    #     print "Error resetting powermeter\n"
    #     sys.exit(2)
        
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
    global lpirc_db
    global enable_powermeter

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hw:p:", ["help", "ip=", "port=", "images=", "result=", \
                                                           "debug", "secret=", \
                                                           "enable_powermeter", \
                                                           "timeout="])
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
        elif switch == "--enable_powermeter":
            enable_powermeter = 1
        else:
            assert False, "unhandled option"

    print "\nhost = "+host_ipaddress+":"+host_port+"\nTest Images = "+\
        test_images_dir_wildcard+"\nTest Result = "+test_result+\
        "\nDebug Mode  = "+mode_debug+"\nTimeout  = "+str(timeout)+\
        "\nDatabase = "+lpirc_db+"\n" 
    if enable_powermeter == 1:
        print "Powermeter Enabled\n"
    else:
        print "Powermeter Disabled\n"        




#++++++++++++++++++++++++++++++++ Parse XML Configuration +++++++++++++++++++++++++++++++
# Main function to parse XML server configuration
def parse_xml_config():

    global host_ipaddress
    global host_port
    global test_images_dir_wildcard
    global test_result
    global mode_debug
    global server_secret_key
    global timeout
    global lpirc_db
    global enable_powermeter

    xml_config_file = os.path.join(this_file_path, './config.xml')
    xml_root = 'Server_Config'
    xml_child = 'Config'
    xml_ipaddress = 'IPaddress'
    xml_port = 'Port'
    xml_image_dir = 'Image_Dir'
    xml_secret_key = 'Secret_Key'
    xml_database_dir = 'Database_Dir'
    xml_debug_mode = 'Debug_Mode'
    xml_timeout = 'Timeout'
    xml_enable_powermeter = 'Enable_Powermeter'

    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_config_file)
        root = tree.getroot()

        host_ipaddress = root.find('./'+xml_child+'/'+xml_ipaddress).text
        host_port = root.find('./'+xml_child+'/'+xml_port).text
        test_images_dir_wildcard = root.find('./'+xml_child+'/'+xml_image_dir).text
        server_secret_key = root.find('./'+xml_child+'/'+xml_secret_key).text
        timeout = int(root.find('./'+xml_child+'/'+xml_timeout).text)
        val = root.find('./'+xml_child+'/'+xml_debug_mode).text
        if val == 'True':
            mode_debug = 'True'
        else:
            mode_debug = 'None'

        val = root.find('./'+xml_child+'/'+xml_enable_powermeter).text
        if val == 'True':
            enable_powermeter = 1
        else:
            enable_powermeter = 0

        print "\nhost = "+host_ipaddress+":"+host_port+"\nTest Images = "+\
            test_images_dir_wildcard+"\nTest Result = "+test_result+"\nDebug Mode  = "+\
            mode_debug+"\nTimeout  = "+str(timeout)+\
            "\nDatabase = "+lpirc_db+"\n" 
        if enable_powermeter == 1:
            print "Powermeter Enabled\n"
        else:
            print "Powermeter Disabled\n"        

    except:
        print "XML Parsing error\n"
            


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

else:
    # Parse XML Config file
    parse_xml_config()
    # Initialize global variables
    init_global_vars()
    # Initialize lpirc session database
    db.create_all()
    # Start server
    app.config["SECRET_KEY"] = server_secret_key



