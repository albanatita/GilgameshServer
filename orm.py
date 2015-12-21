# -*- coding: utf-8 -*-
"""
Created on Tue Oct 13 09:52:58 2015

@author: ekaterina
"""

class Hub():
    
    def __init__(self,hub_ip,hub_port,base_url):
        self.ip=hub_ip
        self.port=hub_port
        self.url=base_url
        
class Spawner():
    
    def __init__(self,usr,hub):
        if usr.activeSession:
            self.activated=True
        self.hub=hub