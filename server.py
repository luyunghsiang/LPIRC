#!/usr/bin/python
import SimpleHTTPServer
import SocketServer
import logging
import cgi
import time
import sys
import random
if len(sys.argv) > 2:
	PORT = int(sys.argv[2])
	I = sys.argv[1]
elif len(sys.argv) > 1:
	PORT = int(sys.argv[1])
	I = ""
else:
	PORT = 8080
	I = ""
	PASSWORD = "magnumopus1234"
	password_approved=0
	image_tag=0
	image_chosen=0
	images_sent = []

class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
	def do_GET(self):
		global image_tag
		global image_chosen
		global images_sent
		global password_approved
		if password_approved > 0:
			#Chooses i_th file randomly from block 5i:5i+5.
			image_chosen = 5*image_tag + random.randrange(1,5)
			images_sent.append(image_chosen)
			for ll in range(0,image_tag):
				print 'image_sent['+str (ll)+'] = '+ str(images_sent[ll])
			#f=open('/home/rgarg/'+str(image_chosen))
			f=open('/home/rgarg/img.jpg')
			#self.wfile.write("%d  " % image_tag)
			self.wfile.write(f.read())
			f.close()
			image_tag=image_tag+1
			#Updates image_tag. Image tag is the index of image being sent to the client.
			#An array images_sent keeps record of the image_sent corresponding to image_tag 
			print image_tag
		else:
			self.wfile.write("Enter the correct password\n")
			print "Enter the correct Password"
		return
	def do_POST(self):
		global password_approved
		global PASSWORD
		global images_sent
		form = cgi.FieldStorage(
			fp=self.rfile,
			headers=self.headers,
			environ={'REQUEST_METHOD':'POST',
				'CONTENT_TYPE':self.headers['Content-Type'],
				})
		#POST accepted only if it has all the 7 fields data. Multiple lines are also accepted.
		image_name = form.getlist("image_name")
		CLASS_ID = form.getlist("CLASS_ID")
		confidence = form.getlist("confidence")
		xmin = form.getlist("xmin")
		ymin = form.getlist("ymin")
		xmax = form.getlist("xmax")
		ymax = form.getlist("ymax")
		#The data will only be written to the file if the password is accepted, all the lines have all the 7 required fields.
		if password_approved and len(image_name)==len(CLASS_ID)==len(confidence)==len(xmin)==len(ymin)==len(xmax)==len(ymax)>0:
			s=""
			#in Case single post has multiple lines, every line is appended to the csv file : out.csv
			for item in range(0,len(ymax)):
				s=s+(image_name[item] + "," + CLASS_ID[item] + "," + confidence[item] + "," + xmin[item] + "," + ymin[item] + "," + xmax[item] + "," + ymax[item] + "\n")
			with open('/home/rgarg/out.csv','a') as fout:
				fout.write(s)	
				fout.close()	
		#Check the PASSWORD
		elif form.getvalue("password") == PASSWORD:
			password_approved = 1
			self.wfile.write("Password Accepted. You can now send Get request for images\n")
			print "Password Accepted"
		else:
			if password_approved: 
				self.wfile.write("Incorrect POST. Make sure that the POST contains all the 7 fields\n")
				print "Incorrect POST. Make sure that the POST contains all the 7 fields\n"
			else:
				print "Enter the correct Password\n"
				self.wfile.write("Enter the correct Password\n")
		SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
Handler = ServerHandler
httpd = SocketServer.TCPServer(("", PORT), Handler)
print "Serving at: http://%(interface)s:%(port)s" % dict(interface=I or "localhost", port=PORT)

httpd.serve_forever()
