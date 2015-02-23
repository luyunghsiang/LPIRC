import pycurl
import pycurl
try:
    # python 3
    from urllib.parse import urlencode
except ImportError:
    # python 2
    from urllib import urlencode

from StringIO import StringIO as BytesIO


from StringIO import StringIO

#login
buffer = StringIO()
c = pycurl.Curl()
c.setopt(c.URL, 'http://127.0.01:5000/login')
post_data = {'username':'lpirc','password':'pass'}
postfields = urlencode(post_data)
c.setopt(c.POSTFIELDS,postfields)
c.setopt(c.WRITEFUNCTION, buffer.write)
c.perform()
c.close()

token = buffer.getvalue()
# Body is a string in some encoding.
# In Python 2, we can print it without knowing what the encoding is.
print(token)


def get_image(token, number):
	c = pycurl.Curl()
	c.setopt(c.URL, 'http://127.0.01:5000/image/?image='+str(number))
	post_data = {'token':token}
	postfields = urlencode(post_data)
	c.setopt(c.POSTFIELDS,postfields)
	with open('image'+str(number)+'.jpg', 'w') as f:
    		c.setopt(c.WRITEDATA, f)
    		c.perform()
    		c.close()

def post_data(token, data):
	c = pycurl.Curl()
	c.setopt(c.URL, 'http://127.0.01:5000/result')
	post_data = {'token':token}
	postfields = urlencode(post_data)+'&'+urlencode(data,True)
	print postfields
	c.setopt(c.POSTFIELDS,postfields)
   	c.perform()
    	c.close()




get_image(token,1)
data = {'image_name':'picasa','CLASS_ID':'12','confidence':'0.3','xmin':'100','ymin':'10','xmax':'500','ymax':'200'}
post_data(token,data)

	
		
