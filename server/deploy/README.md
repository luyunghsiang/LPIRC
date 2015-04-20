# LPIRC Server Deployment


## Requirements
---------------
1. Virtualenv
2. mod_wsgi
3. Apache >2.2


## Deployment
-------------

### Windows 
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
   - pip install <.whl file>
   - Copy generated mod_wsgi.so to modules/ under Apache

7. Edit httpd.conf under C:/Apache24/conf
   - Include <Abs path to lpirc_win32.conf>

8. Check absolute paths under lpirc_win32.conf and deploy.wsgi

9. Check lpirc server configuration (server/source/config.xml)

10. Run Apache
   - C:/Apache24/bin/httpd.exe -k [start|stop|restart]
   - C:/Apache24/bin/httpd.exe -S (Apache status)
   - Error and access log files under C:/Apache24/logs


### Unix 
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
   - Include <Abs path to lpirc_unix.conf>

8. Check absolute paths under lpirc_unix.conf and deploy.wsgi

9. Check lpirc server configuration (server/source/config.xml)

10. Run Apache
   - apachectl -k [start|stop|restart]
   - apachectl -S (Apache status)
   - Error and access log files under /var/log/apache2
