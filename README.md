# LPIRC
Low-Power Image Recognition Challenge

If you have any questions or suggestions, please send email to lpirc@ecn.purdue.edu. Thank you.



## LPIRC Referee Server 
@2015 - HELPS, Purdue University

### TO-DO:
---------
1. Power meter reading
2. Exporting data from database to csv file for post processing



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
2. Send images to token validated client devices upon GET request.
     - The image list in the local directory is refreshed every time before an image is sent.
     - This feature allows image directory to be modified with server running.
3. Receive asynchronous post results for final evaluation.
     - The results are stored in a database.
     - Database allows results to be stored for all users in a single file.
     - Only required user's data is written to a csv file for post processing
4. Get power meter readings from powermeter.
     - Powermeter readings are also stored in the same database.

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
               pip install Flask
               ref: http://flask.pocoo.org/docs/0.10/installation/
      - Flask-Login 
               pip install Flask-Login
      - Flask-SQLAlchemy 
               pip install Flask-SQLAlchemy
               ref: https://github.com/mitsuhiko/flask-sqlalchemy
      - itsdangerous 
               pip install itsdangerous
               ref: http://pythonhosted.org//itsdangerous/

4. Check referee.py for options 
      python referee.py --help
5. Host server 
      python referee.py --ip 127.0.0.1 --port 5000 --images "../images/*.jpg" --timeout 300
       - Hosts server at 127.0.0.1:5000, sending images (*.jpg) to client from directory "../images".
       - Session timeout of 300 seconds


### Usage:
----------
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

            (post)      (token=[token]&..
			             image_name=[image_index])           host/image (Image index starts with 1: 1,2,3,...)
			                                                             Example: curl --data "token=daks....&image_name=3" 127.0.0.1:5000/image

            (post)      (token=[token]&image_name=[image_index]&..
			             CLASS_ID=[id]&confidence=[conf]&..
						 xmin=[xmin]&xmax=[xmax]&..
						 ymin=[ymin]&ymax=[ymax])            host/result
															             Example: curl --data "token=daks....&
																		                       image_name=3&
																							   CLASS_ID=7&
																							   confidence=0.38&
																							   xmin=123.00&xmax=456.00&
																							   ymin=132.00&ymax=756.00"  127.0.0.1:5000/result








### Assumptions:
----------------
1. Image index starts from 1 (not 0).
2. Command line arguments expect to be within quotes
3. Use sql browser to view database (http://sqlitebrowser.org/)


### Power Meter
- To DO
### Matlab Post-Processing
- To DO

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

