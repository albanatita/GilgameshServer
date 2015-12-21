# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 10:47:48 2015

@author: admin
"""

import fileManager as fm
from sqlalchemy import inspect
from sqlalchemy import create_engine


def showDB():
    engine=create_engine(u'mysql+pymysql://ishtar:ishtar@localhost:3306/ishtar',echo=True)
    inspector = inspect(engine)
    for table_name in inspector.get_table_names():
        for column in inspector.get_columns(table_name):
            print("Column: %s" % column['name'])  

def testInitialize():
    fm.initialize()
    showDB()
            
def testaddUser():
    fm.addUser1()
    showDB()

def testDeleteAll():
    fm.deleteAll()
    showDB()

def testShowUser():
    session=fm.session_factory()
    um=fm.userManager()
    um.showUsers(session)

def testgetUser():
    session=fm.session_factory()
    um=fm.userManager()    
    print um.getUser('rdi',session)

def testlistAll():
    session=fm.session_factory()
    um=fm.userManager()    
    usr=um.getUser('rdi',session)
    fman=fm.fileManager(usr,session)
    fman.listAll('/')
    fman.showDirTable()

def testcreateDir():
    session=fm.session_factory()
    um=fm.userManager()    
    usr=um.getUser('rdi',session)
    fman=fm.fileManager(usr,session)   
    fman.create_directory('/dirtoto')    
    fman.create_directory('/dirtoto/dirtotot2')
    fman.create_directory('/dirtoto/dirtotot4')
    fman.create_directory('/dirtotot3')

def testsavefile():
    session=fm.session_factory()
    um=fm.userManager()    
    usr=um.getUser('rdi',session)
    fman=fm.fileManager(usr,session) 
    toto='435804395843095430584305048358034'
    fman.save_file('/dirtoto/testfile34.txt',toto)
    fman.save_file('/dirtoto/testfile1.txt',toto)
    fman.save_file('/dirtoto/dirtotot4/testfile3.txt',toto)
    
def testdeletefile():
    session=fm.session_factory()
    um=fm.userManager()    
    usr=um.getUser('rdi',session)
    fman=fm.fileManager(usr,session) 
    fman.delete_file('/dirtoto/testfile34.txt')

def testrenamedirectory():
    session=fm.session_factory()
    um=fm.userManager()    
    usr=um.getUser('rdi',session)
    fman=fm.fileManager(usr,session)    
    fman.rename_directory('/dirtoto/','/dirtoto0/')


def testrenamefile():
    session=fm.session_factory()
    um=fm.userManager()    
    usr=um.getUser('rdi',session)
    fman=fm.fileManager(usr,session)    
    fman.rename_file('/dirtoto/testfile3.txt','/dirtoto/testtoto34.txt')
    
def testgetfile():
    session=fm.session_factory()
    um=fm.userManager()    
    usr=um.getUser('rdi',session)
    fman=fm.fileManager(usr,session)    
    record= fman.get_file('/dirtoto/testtoto34.txt',content=True)
    print record
    print record.content

def testremovedir():
    session=fm.session_factory()
    um=fm.userManager()    
    usr=um.getUser('rdi',session)
    fman=fm.fileManager(usr,session) 
    fman.delete_directory('/dirtoto/dirtotot4/')

#testDeleteAll()    
#testInitialize()
testaddUser()
#testShowUser()
#testcreateDir()
#testrenamefile()
#testrenamedirectory()
#testlistAll()
#testgetUser()
#testsavefile()
#testgetfile()
#testremovedir()
#testlistAll()