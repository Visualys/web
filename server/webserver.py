#!/usr/bin/env python

#from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import importlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import curdir, sep
import urllib.parse as urllib, json
import cgi
from socketserver import ThreadingMixIn
import threading
import tempfile

class S(BaseHTTPRequestHandler):
    
      
    def do_GET(self):
        message=''
        field = {}
        if self.path=="/": self.path="/hello.html"
        #store field variables
        query = urllib.unquote(self.path).split('?')
        if len(query) > 1:
            query[1]=query[1].split('&')
            for n in range(len(query[1])):
                query[1][n]=query[1][n].split('=')
                field[query[1][n][0]] = query[1][n][1]
        field['host_ip']=self.client_address[0] #special field...
        
        #store cookies to field variables
        cookie_txt=self.headers.get('Cookie')
        if not cookie_txt==None:
            cookie=cookie_txt.split('; ')
            for n in range(len(cookie)):
                cookie[n]=cookie[n].split('=')
                field[cookie[n][0]] = cookie[n][1]

        #redirect to application
        if query[0].endswith('.htm'):
            self.send_response(200)
            self.send_header('content-type', 'text/html;charset=UTF-8')
            self.end_headers()
            f = open(curdir + sep + query[0][1:])
            self.wfile.write(f.read().encode('UTF-8'))
            f.close()
        if query[0].endswith('.js'):
            self.send_response(200)
            self.send_header('content-type', 'text/javascript;charset=UTF-8')
            self.end_headers()
            f = open(curdir + sep + query[0][1:])
            self.wfile.write(f.read().encode('UTF-8'))
            f.close()
        if query[0].endswith('.jpg'):
            self.send_response(200)
            self.send_header('content-type', 'image/jpeg')
            self.end_headers()
            f = open(curdir + sep + query[0][1:],'rb')
            self.wfile.write(f.read())
            f.close()
        if query[0].endswith('.ttf'):
            self.send_response(200)
            self.send_header('content-type', 'font/ttf')
            self.end_headers()
            f = open(curdir + sep + query[0][1:],'rb')
            self.wfile.write(f.read())
            f.close()
        if query[0].endswith('.xlsx'):
            self.send_response(200)
            self.send_header('content-type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            self.end_headers()
            f = open(curdir + sep + query[0][1:],'rb')
            self.wfile.write(f.read())
            f.close()
            
        if query[0].endswith('.exe'):
            appname=query[0][1:-4]
            app = __import__(appname)
            importlib.reload(app) # force reload (not necessary)
            hdr, msg = app.main(field)
            self.send_response(200)
            for x in hdr:
                self.send_header(x[0], x[1])
            self.end_headers()
            self.wfile.write(msg)

        
    def do_POST(self):
        query = urllib.unquote(self.path).split('?')
        field={}
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        # Echo back information about what was posted in the form
        for fld in form.keys():
            fld_item = form[fld]
            if fld_item.filename:
                # The field contains an uploaded file
                file_data = fld_item.file.read()
                file_len = len(file_data)
                temp_name = next(tempfile._get_candidate_names())
                f=open("upload/"+temp_name,"wb")
                f.write(file_data)
                f.close() 
                del file_data
                field[fld]="upload/"+temp_name + '|' + fld_item.filename
            else:
                # Regular form value
                field[fld]=fld_item.value
                #print(fld + '=' + field[fld])

        #store cookies to field variables
        cookie_txt=self.headers.get('Cookie')
        if not cookie_txt==None:
            cookie=cookie_txt.split('; ')
            for n in range(len(cookie)):
                cookie[n]=cookie[n].split('=')
                field[cookie[n][0]] = cookie[n][1]

        if query[0].endswith('.exe'):
            appname=query[0][1:-4]
            app = __import__(appname)
            importlib.reload(app) # force reload (not necessary)
            hdr, msg = app.main(field)
            self.send_response(200)
            for x in hdr:
                self.send_header(x[0], x[1])
            self.end_headers()
            self.wfile.write(msg)
        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
        
def run(server_class=HTTPServer, handler_class=S):
    httpd = ThreadedHTTPServer(('', 80), handler_class)
    print ('Starting httpd...')
    httpd.serve_forever()
    
if __name__ == "__main__":
    from sys import argv
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()


# shared functions

def setcookie(name,value,durhours,durminutes):
    import datetime
    t=['Set-Cookie', name + '=' + value + '; path=/;']
    if durhours+durminutes>0:
        expires = datetime.datetime.utcnow() + datetime.timedelta(hours=durhours, minutes=durminutes)
        t[1]+=" expires=" + expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
    return t
