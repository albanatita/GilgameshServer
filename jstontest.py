# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 12:29:29 2015

@author: admin
"""

import json
from pprint import pprint

with open('C:\\Users\\admin\\AppData\\Roaming\\jupyter\\kernels\\python2\\kernel.json') as data_file:    
    data = json.load(data_file)

pprint(data)
obj=data["env"]["PYTHONPATH"]
print isinstance(obj, basestring) 