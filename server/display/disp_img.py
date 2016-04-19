#!/usr/bin/env python
usage_text = """
LPIRC image display program
=====================
@2016 - HELPS, Purdue University

Main Tasks:
-----------
1. Display images on the monitor.

Requirements:
-------------
1. Windows
2. Python v2.7.3
3. pygtk v2.0

Usage:
------
disp_img.py [OPTIONS]...
Options:
         --images
                Path to the images directory.
"""


import os
import sys
import gtk
import glob
import pygtk
import getopt
import socket
import threading

pygtk.require ('2.0')
gtk.threads_init ()

#++++++++++++++++++++++++++++++++ Global Variables +++++++++++++++++++++++++++++++++++
this_file_path = os.path.dirname (os.path.abspath (__file__))
imgs_path = os.path.join (this_file_path, 'LPIRC/server/shuffle/map0/')

# Script usage function
def usage():
    print usage_text

#++++++++++++++++++++++++++++++++ Socket Listener +++++++++++++++++++++++++++++++++++
# Listens on a port for an image number to be displayed. By default, the port number
# is fixed.
class SocketListener (threading.Thread):

    stop_socket = threading.Event ()        

    def run (self):
        global window
        global image
        #global img_pixmap
        #global img_mask

        self.HOST = 'localhost'
        self.PORT = 50012
        self.s = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind ((self.HOST, self.PORT))
        self.s.listen (1)

        while not self.stop_socket.isSet ():
            conn, addr = self.s.accept ()
            gtk.threads_enter ()
            data = conn.recv (1024)
            print data

            # Changing the image object to the image needed.
            file_name = os.path.join (imgs_path, data + '.jpg')
            pixbuf = gtk.gdk.pixbuf_new_from_file (file_name)
            pixmap, mask = pixbuf.render_pixmap_and_mask ()
            image.set_from_pixmap (pixmap, mask)
            #image.set_from_pixmap (img_pixmap[int (data) - 1], img_mask[int (data) - 1])

            gtk.threads_leave ()
            conn.close ()

        self.s.close ()

    def stop (self):
        self.stop_socket.set ()

def main_quit (obj):
    global server
    server.stop ()
    gtk.main_quit ()

#++++++++++++++++++++++++++++++++ Parse Command-line Input +++++++++++++++++++++++++++++++
# Main function to parse command-line input
def parse_cmd_line():
    global imgs_path
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hw:", ["help", "images="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) 
        usage()
        sys.exit(2)
    for switch, val in opts:
        if switch in ("-h", "--help"):
            usage()
            sys.exit()
        elif switch == "--images":
            imgs_path = val
        else:
            assert False, "unhandled option"

parse_cmd_line ()

# Starting the server thread.
server = SocketListener ()
server.start ()
print "Socket Ready."

# Creating a window object and moving it to the second screen.
window = gtk.Window ()
window.connect ("destroy", main_quit)
window.move (1366, 0)
window.fullscreen ()
image = gtk.Image ()
window.add (image)
window.show_all ()

gtk.main ()
print "Window Ready."