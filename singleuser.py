#!/usr/bin/env python3
"""Extend regular notebook server to be aware of multiuser things."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
try:
    from urllib.parse import quote
except ImportError:
    # PY2 Compat
    from urllib import quote


import config
from jinja2 import ChoiceLoader, FunctionLoader

from tornado import ioloop
#import fileManager
#import checkpoints

from IPython.utils.traitlets import (
    Integer,
    Unicode,
    CUnicode,
)

from IPython.html.notebookapp import NotebookApp, aliases as notebook_aliases


from distutils.version import LooseVersion as V

from pgcontents import PostgresContentsManager
from pgcontents import PostgresCheckpoints
#import fileManager as fm
#import SharedContentsManager

import IPython
if V(IPython.__version__) < V('3.0'):
    raise ImportError("JupyterHub Requires IPython >= 3.0, found %s" % IPython.__version__)

# register new hub related command-line aliases
aliases = dict(notebook_aliases)
aliases.update({
    'user' : 'SingleUserNotebookApp.user',
    'cookie-name': 'SingleUserNotebookApp.cookie_name',
    'hub-prefix': 'SingleUserNotebookApp.hub_prefix',
    'hub-api-url': 'SingleUserNotebookApp.hub_api_url',
    'base-url': 'SingleUserNotebookApp.base_url',
})

page_template = """
{% extends "templates/page.html" %}

{% block header_buttons %}
{{super()}}

<a href='{{central_archive_url}}'
 class='btn btn-default btn-sm navbar-btn pull-right'
 style='margin-right: 4px; margin-left: 2px;' 
 target="_blank"
>
Central archive</a>

<a href='{{bibliography_url}}'
 class='btn btn-default btn-sm navbar-btn pull-right'
 style='margin-right: 4px; margin-left: 2px;'
 target="_blank"
>
Bibiography</a>

<a href='{{hub_control_panel_url}}'
 class='btn btn-default btn-sm navbar-btn pull-right'
 style='margin-right: 4px; margin-left: 2px;'
>
QUIT SESSION</a>
{% endblock %}
{% block logo %}
<img src="/static/title.png"  alt='Gilgamesh'/> <i>powered by</i>
{{super()}}
{% endblock %}
"""

class SingleUserNotebookApp(NotebookApp):
    """A Subclass of the regular NotebookApp that is aware of the parent multiuser context."""

    #fman=fm.fileManager(usr,session) 

    aliases=aliases
    notebook_dir='/'
    open_browser = False
    trust_xheaders = True
    #contents_manager_class=SharedContentsManager.SharedContentsManager  

    #checkpoints_class=checkpoints.NoCheckpoints
    user=CUnicode('rdi',config=True)
    contents_manager_class=PostgresContentsManager
    PostgresContentsManager.db_url = 'postgresql://postgres:ishtar@localhost/ishtar'
    #login_handler_class = JupyterHubLoginHandler
    #logout_handler_class = JupyterHubLogoutHandler


    def _confirm_exit(self):
        # disable the exit confirmation for background notebook processes
        ioloop.IOLoop.instance().stop()
    
    def start(self):
        # Start a PeriodicCallback to clear cached cookies.  This forces us to
        # revalidate our user with the Hub at least every
        # `cookie_cache_lifetime` seconds.
        #self.name=self.session.username
        
        super(SingleUserNotebookApp, self).start()
    
    def init_webapp(self):
        # load the hub related settings into the tornado settings dict
        
        #self.log.info('toto '+str(self.user))        
        #um=fileManager.userManager()  
        #with fileManager.session_scope() as session:
        #	usr=um.getUser(str(self.user),session)
        #	session.expunge(usr)
        #self.log.info('=====> '+str(usr))
        self.checkpoints_class = PostgresCheckpoints

        PostgresContentsManager.user_id = str(self.user)        


        self.log.info('=====> '+str(self.user))
        

#        SharedContentsManager.SharedContentsManager.checkpoints=checkpoints.NoCheckpoints()
#        with fileManager.session_scope() as session:
#            idd=um.getUserID(str(self.user),session)
#            SharedContentsManager.SharedContentsManager.checkpoints.user_id=idd
#            self.log.info('userd id===================>'+str(idd))
        #SharedContentsManager.SharedContentsManager.Session=fileManager.Session
#        SharedContentsManager.SharedContentsManager.fm=fileManager.fileManager(usr)
#        SharedContentsManager.SharedContentsManager.checkpoints.engine=fileManager.engine
        super(SingleUserNotebookApp, self).init_webapp()
        self.patch_templates()
    
    def patch_templates(self):
        """Patch page templates to add Hub-related buttons"""
        env = self.web_app.settings['jinja2_env']
        
        env.globals['hub_control_panel_url'] = config.httpaddress+':8000/shutdown'
        env.globals['central_archive_url'] = config.httpaddress+':8000/shared'
        env.globals['bibliography_url'] = config.httpaddress+':8000/listBiblio'
        
        # patch jinja env loading to modify page template
        def get_page(name):
            if name == 'page.html':
                return page_template
        
        orig_loader = env.loader
        env.loader = ChoiceLoader([
            FunctionLoader(get_page),
            orig_loader,
        ])

    

def main():
    return SingleUserNotebookApp.launch_instance()


if __name__ == "__main__":
    print 'Starting singleuser notebook'
    main()
