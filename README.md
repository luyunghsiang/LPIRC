# LPIRC
Low-Power Image Recognition Challenge

If you have any questions or suggestions, please send email to lpirc@ecn.purdue.edu. Thank you.

To help you test, a web site is available, please do the following

python client.py -w 128.46.75.108 --user lpirc --pass pass


## LPIRC Referee Server 
@2015 - HELPS, Purdue University

### Changes:
-----------
##### 6/1/2015
1. Session logout functionality.
2. Powermeter measurement stop.

##### 5/31/2015
1. client.py - get_image(): image file write from 'w' to 'wb'

##### 5/30/2015
1. Export database entries to csv file for post processing.
2. Dump powermeter readings at an interval of 1 second to database

##### 5/21/2015
1. Powermeter integration.
    - Powermeter executable driver
	- Powermeter python client
2. Logout url
3. Session status entry in database
4. Powermeter driver source code

### Rules:
----------
1. If a single image has multiple bounding boxes, the client can send the bounding boxes in the same POST message.
2. The client may send multiple POST messages for different bounding boxes of the same image.
3. Two different images need to be sent in the different POST messages.
4. The POST messages for different images may be out of order.
   (for example, the bounding boxes for image 5 may be sent before the bounding boxes for image 3)


### Main Tasks:
---------------
1. Authenticate user and provide time limited token for the session.
     - Timeout is set to 5 minutes by default. 
     - If multiple attempts are made to login, all the previous data will be overwritten.
2. Start the powermeter measurements.
     - Powermeter accumulates the energy dissipated for a preset timeout.
3. Send images to token validated client devices upon GET request.
     - JPEG image format (*.jpg)
     - Expects image index between 1 to N (Total images count) from the client.
     - The client can query the available images count.
     - The image list in the local directory is refreshed every time before an image is sent.
     - This feature allows image directory to be modified with server running.
4. Receive asynchronous post results for final evaluation.
     - The results are stored in a database.
     - Database allows results to be stored for all users in a single file.
     - Only required user's data is written to a csv file for post processing
5. Get power meter readings from powermeter.
     - Powermeter readings are also stored in the same database.
6. Stop the powermeter measurements upon timeout or client logout.
7. Compute score based on the mAP and the energy dissipated. 

### Requirements:
-----------------
1. Python v2.7.3
2. Flask v0.10.x - Microframework for Python
3. Flask-SQLAlchemy
4. Flask-Login
5. itsdangerous v0.24


### Installation:
-----------------
1. Install Python v2.7.3
2. Install any Python package manager (example pip)
      ref:https://pip.pypa.io/en/latest/installing.html
3. Install required packages
      - Flask 
       - pip install Flask
       - ref: http://flask.pocoo.org/docs/0.10/installation/
      - Flask-Login 
       - pip install Flask-Login
      - Flask-SQLAlchemy 
       - pip install Flask-SQLAlchemy
       - ref: https://github.com/mitsuhiko/flask-sqlalchemy
      - itsdangerous 
       - pip install itsdangerous
       - ref: http://pythonhosted.org//itsdangerous/

4. Check referee.py for options 
      python referee.py --help
5. Host server (Debug mode)
      python referee.py --ip 127.0.0.1 --port 5000 --images "../images/*.jpg" --timeout 300
       - Hosts server at 127.0.0.1:5000, sending images (*.jpg) to client from directory "../images".
       - Session timeout of 300 seconds


### Usage:
----------
referee.py [OPTION]

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

         --enable_powermeter
                Enables powermeter

         -h, --help
                Displays all the available option


### Following URLs are recognized, served and issued:
-----------------------------------------------------
            (post/get)     --NA--                            host/
			                                                             Example: curl 127.0.0.1:5000/

            (post/get)     --NA--                            host/help
			                                                             Example: curl 127.0.0.1:5000/help

            (post)      (username=[user]&password=[pass])    host/login
			                                                             Example: curl --data "username=user&password=pass" 127.0.0.1:5000/login

            (post)      (token=[token])                      host/verify
			                                                             Example: curl --data "token=daksldjsaldkjlkj32....." 127.0.0.1:5000/verify

            (post)      (token=[token])                      host/logout
			                                                             Example: curl --data "token=daksldjsaldkjlkj32....." 127.0.0.1:5000/logout

            (post)      (token=[token])                      host/no_of_images
			                                                             Example: curl --data "token=daksldjsaldkjlkj32....." 127.0.0.1:5000/no_of_images

            (post)      (token=[token]&image_name=[image_index])  host/image (Image index starts with 1: 1,2,3,...)
			                                                             Example: curl --data "token=daks....&image_name=3" 127.0.0.1:5000/image

            (post)      (token=[token]&image_name=[image_index]&..
			             CLASS_ID=[id]&confidence=[conf]&..
						 xmin=[xmin]&xmax=[xmax]&..
						 ymin=[ymin]&ymax=[ymax])            host/result
																		Example: curl --data "token=daks....&image_name=3&
																		                       CLASS_ID=7&confidence=0.38&
																							   xmin=123.00&xmax=456.00&
																							   ymin=132.00&ymax=756.00"     127.0.0.1:5000/result

            (post)      (token=[token]&player=[player_name]&..
			             voltage=[voltage]&current=[current]&..
						 power=[power]&energy=[energy]&..
						 elapsed=[elapsed_time])            host/powermeter
																		Example: curl --data "token=daks....&player=lpirc&
																							  voltage=120&current=0.1&
																							  power=9&energy=45&
																							  elapsed=5"     127.0.0.1:5000/powermeter

            (post)      (token=[token]&player=[player_name])  host/savecsv (All submissions saved if no player_name)
			                                                             Example: curl --data "token=daks....&player=lpirc" 127.0.0.1:5000/savecsv



### Note:
---------
1. Image format: JPEG (*.jpg, *.JPEG)
2. Image index starts from 1 (not 0).
3. Command line arguments expect to be within quotes
4. Use sql browser to view database (http://sqlitebrowser.org/)


### Sample Client
Sample Client performs the following operations:

- POSTS username and password to start a session with the server
- POSTS the bounding box information to the server.
- Requests for the images and stores locally.

Additional Notes: 

-Sample Client uses a file "golden_output.csv" which contains list of 
bounding box information corresponding to the test images in the server.
This file is being used to simulate the recognition program the
participant will have during the competition. This is just sample data
to check if the interface with the server is working properly.
The participant should generate this data by running the recognition software
on the images sent by the server. 

-client/temp is temporary directory.
Images are buffered in this directory, and removed immediately after that.
Images are copied to the 'images' directory if and only if, Server replies with OK status (200). 



### Deployment
-------------

#### Windows 
-----------
1. Install Python v2.7.3

2. Install pip
   Ref: http://flask.pocoo.org/docs/0.10/installation/#windows-easy-install

3. Install Virtualenv
   - pip install virtualenv
   - mkdir myproject
   - cd myproject
   - virtualenv venv
   - venv\scripts\activate
   
4. Install required packages
   - Flask 
     - pip install Flask
     - ref: http://flask.pocoo.org/docs/0.10/installation/
   - Flask-Login 
     - pip install Flask-Login
   - Flask-SQLAlchemy 
     - pip install Flask-SQLAlchemy
     - ref: https://github.com/mitsuhiko/flask-sqlalchemy
   - itsdangerous 
     - pip install itsdangerous
     - ref: http://pythonhosted.org//itsdangerous/

5. Download Apache
   Ref: https://www.apachehaus.com/cgi-bin/download.plx
   - Move Apache24 to C:/

6. Install mod_wsgi
   Ref: http://www.lfd.uci.edu/~gohlke/pythonlibs/#mod_wsgi
   - pip install (.whl file)
   - Copy generated mod_wsgi.so to modules/ under Apache

7. Edit httpd.conf under C:/Apache24/conf
   - Include Abs path to lpirc_win32.conf

8. Check absolute paths under lpirc_win32.conf and deploy.wsgi

9. Check lpirc server configuration (server/source/config.xml)

10. Run Apache
   - C:/Apache24/bin/httpd.exe -k [start|stop|restart]
   - C:/Apache24/bin/httpd.exe -S (Apache status)
   - Error and access log files under C:/Apache24/logs


#### Unix 
-----------
1. Install Python v2.7.3

2. Install pip
   Ref: http://flask.pocoo.org/docs/0.10/installation/#windows-easy-install

3. Install Virtualenv
   - pip install virtualenv
   - mkdir myproject
   - cd myproject
   - virtualenv venv
   - . venv/bin/activate
   
4. Install required packages
   - Flask 
     - pip install Flask
     - ref: http://flask.pocoo.org/docs/0.10/installation/
   - Flask-Login 
     - pip install Flask-Login
   - Flask-SQLAlchemy 
     - pip install Flask-SQLAlchemy
     - ref: https://github.com/mitsuhiko/flask-sqlalchemy
   - itsdangerous 
     - pip install itsdangerous
     - ref: http://pythonhosted.org//itsdangerous/

5. Download Apache

6. Install mod_wsgi

7. Edit apache2.conf under /etc/apache2/
   - Include (Abs path to lpirc_unix.conf)

8. Check absolute paths under lpirc_unix.conf and deploy.wsgi

9. Check lpirc server configuration (server/source/config.xml)

10. Run Apache
   - apachectl -k [start|stop|restart]
   - apachectl -S (Apache status)
   - Error and access log files under /var/log/apache2

