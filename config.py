# -*- coding: utf-8 -*-
"""
Created on Sat Nov 28 15:03:26 2015

@author: rdi

Configuration file
Mostly define paths and database
"""

import os

ip='130.183.52.47'
#ip='localhost'
httpaddress="http://"+ip
reqport=8001
gilgapath=r'C:\ISHTAR\gilgameshServer'
gilgalibpath=r'C:\ISHTAR'
#gilgapath='/home/rdi/gilgameshServer'

proxycmd='node C:\ISHTAR\gilgameshServer\configurable-http-proxy-master\\bin\configurable-http-proxy '
#proxycmd='nodejs /home/rdi/gilgameshServer/configurable-http-proxy-master/bin/configurable-http-proxy '
filerepos='C:'+os.sep+'ISHTAR'+os.sep+'tmp'+os.sep
#filerepos='/home/rdi/repos/'
dburl=u'mysql+pymysql://ishtar:postgres:ishtar@localhost/ishtar'