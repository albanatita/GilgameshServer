# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 13:01:46 2015

@author: rdi

Tornado server to control the request on the principal address and port 

"""


from tornado.escape import json_decode
import os
import json
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
import config
import pgcontents.query as pgquery
from pgcontents.api_utils import to_api_path,split_api_filepath
from subprocess import Popen
import tornado.httpserver
import tornado.options
from tornado.ioloop import IOLoop
import signal
from tornado import gen, web
import time
from traitlets.config import Application
import pickle
import testUser
#from sqlalchemy.engine.base import Engine
from sqlalchemy import create_engine
from nbconvert import HTMLExporter
import HTMLParser
from pgcontents.api_utils import reads_base64
import bibtexparser as bib

here = os.path.dirname(__file__) # TODO: files are all gathered together. Clean the file structure


#import fileManager
#import singleuser
#import SharedContentsManager



# 
class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

# Manage Login page
class LoginHandler(BaseHandler):
    def get(self):
        self.render(here+"/login.html")

# Check if the user exist + general password
# if yes, create a secure cookie to identify the user locally
    def post(self):

        db=create_engine('postgresql://postgres:ishtar@localhost/ishtar')
        passwd=self.get_argument("password")
        if testUser.usr_exists(db,self.get_argument("name")) and passwd=='ishtar':
			self.set_secure_cookie("user", self.get_argument("name"))
        db.dispose()
        self.redirect("/")

# Logout handler       
class LogoutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        name = tornado.escape.xhtml_escape(self.current_user)
        self.write("Goodbye, " + name)
        self.clear_cookie("user")
        self.application.srvTable[name]=0
        table=self.application.srvTable
        with open(config.gilgapath+os.sep+'srvTable.pickle', 'wb') as handle:
                pickle.dump(table, handle)

# called only by the admin rdi: kill process: node.js
class DisconnectHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        name = tornado.escape.xhtml_escape(self.current_user)
        if name=='rdi':
            os.kill(self.application.nodepid, signal.SIGINT)
        else:
            pass
        self.redirect("/")

# called to stop the Jupyter instance of one user
class ShutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        name = tornado.escape.xhtml_escape(self.current_user)
        pid=self.application.srvTable[name]
        os.kill(pid, signal.SIGINT)
        client=AsyncHTTPClient()
        req = HTTPRequest(config.httpaddress+':'+str(config.reqport)+'/api/routes/'+name,
            method='DELETE',
            headers={'Authorization': 'token '+format(self.application.auth_token)}, #.format(self.application.auth_token)
        )
        client.fetch(req)
        self.application.srvTable[name]=0
        table=self.application.srvTable
        with open(config.gilgapath+os.sep+'srvTable.pickle', 'wb') as handle:
                pickle.dump(table, handle)
        self.redirect('/logout')
 
# List users in activity
class ListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        kwargs = {'table': self.application.srvTable}
        name = tornado.escape.xhtml_escape(self.current_user)
        if name=='rdi':
            self.render('listUsers.html',**kwargs)
            
    @tornado.web.authenticated   
    def post(self):
          name=self.get_argument("value")
          nameusr = tornado.escape.xhtml_escape(self.current_user)
          if nameusr=='rdi':
              try:
                  pid=self.application.srvTable[name]
                  os.kill(pid, signal.SIGINT)   
                  client=AsyncHTTPClient()
                  req = HTTPRequest(config.httpaddress+':'+str(config.reqport)+'/api/routes/'+name,
                                    method='DELETE',
                                    headers={'Authorization': 'token '+format(self.application.auth_token)}, #.format(self.application.auth_token)
                                    )
                  client.fetch(req)
                  self.application.srvTable[name]=0
              except:
                  self.write("Error killing user "+name)
                  self.application.srvTable[name]=0
              table=self.application.srvTable
              with open(config.gilgapath+os.sep+'srvTable.pickle', 'wb') as handle:
                pickle.dump(table, handle)
              self.redirect('/listUsers')

def TreeFile(db,path):
    liste=pgquery.directories_in_directory(db, 'share', path)
    text='<ul>\n'
    for n in liste:
        text=text+'<li id='+n['name']+'>'+split_api_filepath(to_api_path(n['name']))[1]+'\n'
        text2=TreeFile(db,n['name'])
        text=text+text2
    liste=pgquery.files_in_directory(db, 'share', path)
    for n in liste:
        text=text+'<li id='+path+n['name']+' data-jstree=''{"icon":"/static/file-icon.png"}''>'+split_api_filepath(to_api_path(n['name']))[1]+'</li>\n'
    text=text+'</ul>\n'
    text=text+'</li>\n'
    return text 

class RenderHandler(BaseHandler):
        @tornado.web.authenticated
        def post(self): 
          id=self.get_argument("path")
          print id
          db=create_engine('postgresql://postgres:ishtar@localhost/ishtar')
        
          fileContent=reads_base64(pgquery.get_file(db, "share", id, include_content=True)['content'])
          #notebook= nbformat.reads(fileContent, as_version=4)
          notebook=fileContent
          db.dispose()
          html_exporter = HTMLExporter()
          html_exporter.template_file = 'basic'

          (body, resources) = html_exporter.from_notebook_node(notebook)
          self.write(body)


class PullHandler(BaseHandler):
        @tornado.web.authenticated
        def post(self): 
            name = tornado.escape.xhtml_escape(self.current_user)
            path=self.get_argument("path")
            db=create_engine('postgresql://postgres:ishtar@localhost/ishtar')
            binarycontent=pgquery.get_file(db, "share", path, include_content=True)['content']   
            db.dispose()
            with create_engine('postgresql://postgres:ishtar@localhost/ishtar').begin() as db:
                pgquery.save_file(db, name, '/export/'+split_api_filepath(path)[1], binarycontent, 0)
            self.redirect('/shared')

class PushHandler(BaseHandler):
        @tornado.web.authenticated
        def post(self): 
            usr= tornado.escape.xhtml_escape(self.current_user)
            #print "I got a request!"
            #print self.request.arguments
            file='/'+self.get_argument("file")
            name=split_api_filepath(file)[1]
            db=create_engine('postgresql://postgres:ishtar@localhost/ishtar')
            binarycontent=pgquery.get_file(db, usr, file, include_content=True)['content'] 
            db.dispose()
            with create_engine('postgresql://postgres:ishtar@localhost/ishtar').begin() as db:
                pgquery.save_file(db, 'share', '/export/'+name, binarycontent, 0)
            #self.write('File shared')

class SharedHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self): 
        db=create_engine('postgresql://postgres:ishtar@localhost/ishtar')
        tree=TreeFile(db,'/')
        h= HTMLParser.HTMLParser()
        tree=h.unescape(tree)
        db.dispose()
        #self.render('shared.html')
        kwargs={'tree':tree}
        self.render('shared.html',autoescape=None,**kwargs)

class SendBiblioHandler(BaseHandler):
        @tornado.web.authenticated
        def post(self):     
            print "I got a request!"          
            liste=json_decode(self.get_argument("list"))
            with open('listb.bib') as bibtex_file:
                bibtex_str = bibtex_file.read()
        
            database = bib.loads(bibtex_str).entries
            output=[]
            for entry in liste:             
             output.append((item for item in database if item["ID"] == entry).next())
            self.write(json.dumps(output))
    
class BiblioHandler(tornado.web.RequestHandler):
     @tornado.web.authenticated
     def post(self):    
         with open('listb.bib') as bibtex_file:
             bibtex_str = bibtex_file.read()
        
         bib_database = bib.loads(bibtex_str)
         kwargs = {'table': {(d['ID'],d['title'],d['author']) for d in bib_database.entries}}
         self.render('listBiblio.html',**kwargs)

class AddBiblioHandler(BaseHandler):
     @tornado.web.authenticated
     def post(self):     
        pass
    
# if user identified with cookie, it asks the proxy to redirect the calls on 8000 to the Jupyter server identified with a port number   
 # then it starts the Jupyter server
class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        name = tornado.escape.xhtml_escape(self.current_user)
        table=self.application.usrTable
        port=table[name] 
        if self.application.srvTable[name]==0:
            body=dict(
            target=config.httpaddress+':'+str(port)
            )
            body = json.dumps(body)
            client=AsyncHTTPClient()
            req = HTTPRequest(config.httpaddress+':'+str(config.reqport)+'/api/routes/'+name,
                method='POST',
                headers={'Authorization': 'token '+format(self.application.auth_token)}, #.format(self.application.auth_token)
                body=body
            )
            
            client.fetch(req)
            cmd=[r'python']
            argscmd=[config.gilgapath+os.sep+'start-singleuser.py','--profile=admin','--debug','--base-url=/'+name,'--port='+str(port),'--user='+name,'--ip='+config.ip]
            cmd.extend(argscmd)
            #session=fm.session_factory()
#            print cmd
            env=os.environ.copy()     
            env["PATH"] = config.gilgapath + ';'+env["PATH"]
            env["PATH"] = config.gilgalibpath + ';'+ env["PATH"]
            env["PYTHONPATH"]=config.gilgalibpath+';'+ env["PATH"]
            env['USRGILGA']=name
            res=Popen(cmd,env=env)
            self.application.srvTable[name]=res.pid
            #out, err = res.communicate()
            time.sleep(6) #TODO: not very efficient: we wait 6 seconds, for the Jupyter notebook to start.
            table=self.application.srvTable
            with open(config.gilgapath+os.sep+'srvTable.pickle', 'wb') as handle:
                pickle.dump(table, handle)
        self.redirect("/"+name)        
        
        #self.write("Hello, " + name)

# The main class to start the central server
class serverHub(Application):
#TODO: clean all thee parameters
    port=8000
    hub_port=8888
    ip=config.ip
    auth_token = 'ishtarforever'
    hub_ip=config.ip
    hub_prefix='/'
    base_url='/'
    proxy_api_ip=config.ip
    proxy_api_port=config.reqport
    proxy_cmd=config.proxycmd
    proxy_auth_token='ishtarforever'
    handlers=[(r"/", MainHandler),
    (r"/login", LoginHandler),
    (r"/logout",LogoutHandler),
    (r"/disconnect",DisconnectHandler),
    (r"/shutdown",ShutHandler),
    (r"/listUsers",ListHandler),
    (r"/shared",SharedHandler),
    (r"/render",RenderHandler),
    (r"/pull",PullHandler),
    (r"/push",PushHandler),
    (r"/listBiblio",BiblioHandler),
    (r"/addBiblio",AddBiblioHandler),
    (r"/sendBiblio",SendBiblioHandler),
    (r"/static/(.*)",tornado.web.StaticFileHandler, {"path": here},)
]

# we initialize here the list of active users and the associated list of ports
    def init_hub(self):
        db=create_engine('postgresql://postgres:ishtar@localhost/ishtar')
        listUsr=testUser.usr_list(db)
        db.dispose()
        nlength=len(listUsr)
        print '++++++>'+str(nlength)
        listePorts=range(8100,8100+nlength)
        self.usrTable=dict(zip(listUsr,listePorts))
        try:
            with open(config.gilgapath+os.sep+'srvTable.pickle', 'rb') as handle:
                table = pickle.load(handle)
                self.srvTable=table
                print table
        except:
            self.srvTable=dict(zip(listUsr,[0]*len(listUsr)))

# we initialize the userManager
    @gen.coroutine
    def init_users(self):
        #self.um=fileManager.userManager()
        pass

# we configure the parameters of the nodes.js proxy server
    def init_proxy(self):
        """Load the Proxy config into the database"""
        self.proxy_auth_token = self.proxy_auth_token # not persisted
        self.proxy_log = self.log
        self.proxy_ip = self.ip
        self.proxy_port = self.port
        self.proxy_api_ip = self.proxy_api_ip
        self.proxy_api_port = self.proxy_api_port
        self.proxy_api_url = '/api/routes/'
        os.environ['CONFIGPROXY_AUTH_TOKEN']=self.auth_token
        

# the proxy node.js is started here
    def start_proxy(self):
		"""Actually start the configurable-http-proxy"""
		# check for proxy     
		os.environ['CONFIGPROXY_AUTH_TOKEN'] = self.proxy_auth_token
		env=os.environ.copy()
		cmd = self.proxy_cmd +'--ip '+ str(self.proxy_ip)+' --port '+ str(self.proxy_port)+' --api-ip '+ str(self.proxy_api_ip)+' --api-port '+ str(self.proxy_api_port)+ ' --default-target http://'+config.ip+':'+ str(self.hub_port)
		print cmd
		self.proxy_process = Popen(cmd,env=env,shell=True)
        
# Initialize the parameters of the main Tornado server
    def init_tornado_settings(self):
        """Set up the tornado settings dict."""
        #base_url = self.hub.server.base_url
        self.settings = {
        "cookie_secret": "ishtar_forever_458932",
        "login_url": "/login",
        "static_path": here
        }
#        self.login_url = 'login'
#        self.logout_url = 'logout'
        

        #self.tornado_settings = settings

    def init_tornado_application(self):
        """Instantiate the tornado Application object"""
        self.tornado_application = web.Application(self.handlers,**self.settings)
        self.tornado_application.listen(8888)
        self.tornado_application.usrTable=self.usrTable
        self.tornado_application.srvTable=self.srvTable
        self.tornado_application.auth_token=self.auth_token
        self.tornado_application.nodepid=self.proxy_process.pid

    @gen.coroutine
    def initialize(self, *args, **kwargs):
        #super().initialize(*args, **kwargs)
        #self.session=fileManager.session_factory()
        yield self.init_users()
        self.init_hub()
        self.init_proxy()
        self.start_proxy()
        #yield self.init_spawners()

        self.init_tornado_settings()
        self.init_tornado_application()
 
    @gen.coroutine       
    def start(self):
        """Start the whole thing"""
        self.io_loop =  IOLoop.current()
        
# Start asynchronous operations of the Tornado server
    @gen.coroutine
    def launch_instance_async(self, argv=None):
        try:
            yield self.initialize(argv)
            yield self.start()
        except Exception as e:
            self.log.exception(e)
            self.exit(1)

# Start the main Tornado loop
    @classmethod
    def launch_instance(cls, argv=None):
        self = cls.instance()
        loop = IOLoop.current()
        loop.add_callback(self.launch_instance_async, argv)
        try:
            loop.start()
        except KeyboardInterrupt:
            print("\nInterrupted")    

main = serverHub.launch_instance()

if __name__ == "__main__":
    main()
