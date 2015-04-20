import sys,os
print >> sys.stderr, 'IMPORTING WSGI SCRIPT FILE'

if sys.platform == 'win32':
   abs_path_venv = 'C:/Work/vpyenv/venv/Scripts/activate_this.py'
   abs_path_source = 'C:/Work/Dropbox/LPIRC/server/source'
else:
   abs_path_venv = '/home/ganesh/vpyenv/venv/bin/activate_this.py'
   abs_path_source = '/home/ganesh/Dropbox/LPIRC/server/source'


activate_this = abs_path_venv
execfile(activate_this, dict(__file__=activate_this))

sys.stdout = sys.stderr

sys.path.insert(0, abs_path_source)

from referee import app as application