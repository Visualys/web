#!/usr/bin/env python

import importlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import curdir, sep
import urllib.parse as urllib
import cgi
from socketserver import ThreadingMixIn
import threading
import tempfile
import sqlite3, json, requests

content_type={'htm':'text/html;charset=UTF-8',
              'ico':'image/x-icon',
              'js':'text/javascript;charset=UTF-8',
              'jpg':'image/jpeg',
              'png':'image/png',
              'ttf':'font/ttf',
              'xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
              }
cache_control={'ttf':'max-age=2592000',
               'js': 'max-age=2592000',
               'ico':'max-age=2592000',
               }
import _thread
from scripts.action_trigger import action_trigger
from scripts.radio import webradio
try:
    radio = webradio()
    radio.open('antenne bayern','chillout')
    radio.stop()
    radio.setvolume(50)
except:
    pass

class S(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=="/": self.path="/index.htm"
        #store field variables
        field = {}
        query = urllib.unquote(self.path).split('?')
        if len(query) > 1:
            query[1]=query[1].split('&')
            for n in range(len(query[1])):
                query[1][n]=query[1][n].split('=')
                if len(query[1][n])==2:
                    field[query[1][n][0]] = query[1][n][1]
        field['host_ip']=self.client_address[0] #special field...
        #store cookies to field variables
        cookie_txt=self.headers.get('Cookie')
        if not cookie_txt==None:
            cookie=cookie_txt.split('; ')
            for n in range(len(cookie)):
                cookie[n]=cookie[n].split('=')
                field[cookie[n][0]] = cookie[n][1]
        extension = query[0].split('.')[-1]
        if extension in content_type:
            self.send_response(200)
            self.send_header('content-type', content_type[extension])
            if extension in cache_control:
                if '/js/'in query[0]:
                    self.send_header('cache-control', 'max-age=2592000') # 30 jours
                else:
                    self.send_header('cache-control', cache_control[extension])
            self.end_headers()
            f = open(curdir + sep + query[0][1:], 'rb')
            self.wfile.write(f.read())
            f.close()
        elif extension == 'db':
            dbname=query[0][1:]
            db = sqlite3.connect(dbname)
            cur = db.cursor()
            cur.execute("SELECT mime,cache,file,mime FROM files WHERE filename=?", (field['file'],))
            r = cur.fetchone()
            self.send_response(200)
            self.send_header('content-type', r[0])
            self.send_header('cache-control', 'max-age='+r[1])
            self.end_headers()
            self.wfile.write(bytes(r[2], 'utf-8'))
            db.close()

        elif query[0]=='/dmx':
            if('mes' in field):
                x = field['mes'].split(',')
                if len(x)>=2 and len(x) % 2 == 0:
                    db = sqlite3.connect('dmx.db')
                    cur = db.cursor()
                    for x2 in range(0,len(x),2):
                        cur.execute('UPDATE capteurs set val=?, ip=? where num=?',(x[x2+1], field['host_ip'], x[x2],))
                        _thread.start_new_thread(action_trigger, (x[x2], x[x2+1]))
                    db.commit()
                    self.send_response(200)
                    self.send_header('content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(bytes('dmx:ok', 'utf-8'))
                    db.close()
            elif('sw' in field):
                    db = sqlite3.connect('dmx.db')
                    cur = db.cursor()
                    cur.execute('SELECT val,ip,unite FROM capteurs WHERE num=?', (field['sw'],))
                    s = cur.fetchone()
                    if s[0] is None:
                        x = 1
                    else:
                        x = 1 - int(s[0])
                    if s[2]==15: #rf433
                        cur.execute('SELECT capteurs.ip FROM rf JOIN capteurs ON capteurs.num=rf.gatenum WHERE rf.num=?', (field['sw'],))
                        s2 = cur.fetchone()
                        r = requests.get('http://%s/%s,%s' % (s2[0], field['sw'],x), timeout=3)
                    elif field['sw']=='36': #wifi
                        r = requests.get('http://%s/%s' % (s[1],x), timeout=3)
                    else:
                        r = requests.get('http://%s/control?cmd=event,sw=%s' % (s[1],x), timeout=2)
                    self.send_response(200)
                    self.send_header('content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(bytes(str(x), 'utf-8'))
                    db.close()

        elif extension == 'exe':
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
                field[fld] = urllib.unquote(fld_item.value)

        #store cookies to field variables
        cookie_txt=self.headers.get('Cookie')
        if not cookie_txt==None:
            cookie=cookie_txt.split('; ')
            for n in range(len(cookie)):
                cookie[n]=cookie[n].split('=')
                field[cookie[n][0]] = cookie[n][1]
        extension = query[0].split('.')[-1]
        if extension == 'db':
            dbname=query[0][1:]
            db = sqlite3.connect(dbname)
            cur = db.cursor()
            cur.execute(field['q'])
            if cur.rowcount>0:
                db.commit()
                r='[]'
            else:
                r = json.dumps(cur.fetchall(), separators=(',', ':'))
            self.send_response(200)
            self.send_header('content-type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(r, 'utf-8'))
            db.close()
        elif query[0]=='/dmx':
            if('sw' in field):
                    db = sqlite3.connect('dmx.db')
                    cur = db.cursor()
                    cur.execute('SELECT val,ip,unite FROM capteurs WHERE num=?', (field['sw'],))
                    s = cur.fetchone()
                    if s[0] is None:
                        x = 1
                    else:
                        x = 1 - int(s[0])
                    if s[2]==15: #rf433
                        cur.execute('SELECT capteurs.ip FROM rf JOIN capteurs ON capteurs.num=rf.gatenum WHERE rf.num=?', (field['sw'],))
                        s2 = cur.fetchone()
                        r = requests.get('http://%s/%s,%s' % (s2[0], field['sw'],x), timeout=3)
                    elif field['sw']=='36': #wifi
                        r = requests.get('http://%s/%s' % (s[1],x), timeout=3)
                    else:
                        r = requests.get('http://%s/control?cmd=event,sw=%s' % (s[1],x), timeout=2)
                    self.send_response(200)
                    self.send_header('content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(bytes(str(x), 'utf-8'))
                    db.close()
        elif query[0]=='/dmx/radio':
            if field['cmd']=='status':
                self.send_response(200)
                self.send_header('content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes(json.dumps(radio.getmetadata()), 'utf-8'))
            else:
                if field['cmd']=='play':
                    t = field['radio'].split(' - ')
                    radio.open(t[0],t[1])
                    radio.play()
                elif field['cmd']=='stop':
                    radio.stop()
                elif field['cmd']=='vol':
                    radio.setvolume(int(field['v']))
                elif field['cmd']=='eq':
                    t=[0,0,0,0,0,0,0,0,0,0]
                    for n in range(10):
                        t[n]=float(field['e{}'.format(n)])
                    radio.seteq(t)
                self.send_response(200)
                self.send_header('content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes('dmx:ok', 'utf-8'))
        elif extension == 'exe':
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
        
def run(server_class=HTTPServer, handler_class=S, port=8080):
    httpd = ThreadedHTTPServer(('', port), handler_class)
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
