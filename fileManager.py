# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 11:47:08 2015

@author: rdi

The virtual file and user manager system
"""

from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref,sessionmaker
from sqlalchemy import Column, Integer, String, DateTime,Boolean
import os
import datetime
import config
from contextlib import contextmanager
from base64 import (
    b64decode,
    b64encode,
)
Base = declarative_base()

def session_factory(url=config.dburl):
     engine=create_engine(url,pool_recycle=3600)
     Session=sessionmaker(bind=engine)
     return Session
     
Session=session_factory()

def writes_base64(nb):
    """
    Write a notebook as base64.
    """
    #return b64encode(nb.encode('utf-8'))
    return b64encode(nb)

@contextmanager
def session_scope():
	session=Session()
	try:
		yield session
		session.commit()
	except:
		session.rollback()
		raise
	finally:
		session.close()

class File(Base):
    __tablename__='files'
    id=Column(Integer,primary_key=True)
    name=Column(String(255))
    savedName=Column(String(255))
    author=Column(String(255))
    modified_author=Column(String(255),default='')
    version=Column(Integer,default='1')
    subversion=Column(Integer,default='0')
    created=Column(DateTime,default=datetime.datetime.now)
    modified=Column(DateTime,onupdate=datetime.datetime.now)
    directory_id=Column(Integer,ForeignKey('directories.id'))
    directory=relationship("Directory",backref=backref('files',order_by=id),cascade='all,delete')
    typeFile=Column(String(255),default='')
    ref=Column(String(255),default='')
    owner_id=Column(Integer,ForeignKey('users.id'))
    
    def __repr__(self):
        return "<File(name='%s')>" % (self.name)

class Directory(Base)  :
    __tablename__='directories'
    id=Column(Integer,primary_key=True)
    name=Column(String(255))
    parent_id=Column(Integer)
    owner_id=Column(Integer,ForeignKey('users.id'))

    def __repr__(self):
        return "<Directory(id='%s', name='%s', owner_id='%s', files='%s')>" % (self.id,self.name,self.owner_id,self.files)

class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True)
    name=Column(String(255))
    password=Column(String(255))
    role=Column(String(255))
    sessionActive=Column(Boolean)
    sessionPort=Column(Integer)

    def __repr__(self):
        return "<User(name='%s')>" % (self.name)

class userManager():
    
    def addUser(self,name,password,role,session):
        usr=User(name=name,password=password,role=role)
        if session.query(User.id).filter(User.name==usr.name).count()==0:    
            session.add(usr)
            session.commit()
            return usr
        else:
            print "User with same name exists"

    def showUsers(self,session):
        for usr in session.query(User):
            print usr
    def userList(self,session):
        list=[]
        for usr in session.query(User):
           list.append(usr.name) 
        return list
            
    def getUser(self,name,session):
        return session.query(User).filter(User.name==name).first()
        
    def existUser(self,name,session):
        return session.query(User.id).filter(User.name==name).count()==1

um=userManager()

class fileManager():
    
    def __init__(self,user):
        self.user=user
        self.repos=config.filerepos

    def showDirTable(self,session):
        for dir in session.query(Directory):
            print dir
    
    def createRoot(self,session):
        direct=Directory(name="/",parent_id=-1,owner_id=self.user.id)
        session.add(direct)

   
    def getDirfromPath(self,path,session)    :
        if path[-1] !='/':
            path=path+'/'
        return session.query(Directory).filter(Directory.name==path).filter(Directory.owner_id==self.user.id).one()
    
    def getFilefromPath(self,path,session)    :
        return session.query(File).filter(File.name==path).filter(Directory.owner_id==self.user.id).one()    
    
    def getsubdirs(self,record,session):
        return session.query(Directory).filter(Directory.parent_id==record.id,Directory.owner_id==self.user.id).all()
    
    def getName(self,path) :
        if path[-1]=='/':
            return path.rsplit('/', 2)[-2]
        else:
            return path.rsplit('/',1)[-1]
    
    def listAll(self,path,session,prefix=''):
        if self.dir_exists(path,session):
            prefix=prefix+'-'
            dir=self.getDirfromPath(path,session)
            for files in dir.files:      
                try:                
                    print prefix+' '+self.getName(files.name)
                except:
                    pass
            for subdir in session.query(Directory).filter(Directory.parent_id==dir.id).filter(Directory.owner_id==self.user.id).all():
                print prefix+' '+self.getName(subdir.name)
                self.listAll(subdir.name,session,prefix=prefix)
        else:
            print "directory does not exist"
    
    def dir_exists(self,path,session):
        print path
        if path=='':
            path='/'
        if path[-1] !='/':
            path=path+'/'
        return session.query(Directory).filter(Directory.name==path).filter(Directory.owner_id==self.user.id).count()
        
    def file_exists(self,path,session):
        return session.query(File.id).filter(File.name==path,Directory.owner_id==self.user.id).count()>0
        
       
    def delete_directory(self,path,session):
        if path[-1] !='/':
            path=path+'/'
        if self.dir_exists(path,session):     
           dir=self.getDirfromPath(path,session)
           filelist=dir.files
           session.delete(dir)   
           session.commit()
           for files in filelist:      
                try:                
                    self.delete_file(files.name,session)
                except:
                    pass 

        else:
            print 'Directory does not exist'
        
    def delete_file(self,path,session):
        if self.file_exists(path,session):
            file=self.getFilefromPath(path,session)
            savedname=file.savedName
            session.delete(file)
            session.commit()
            try:
                os.remove(self.repos+savedname)
                return True
            except:
                print "Impossible to delete the physical file"
                return False
            
    
    def rename_directory(self,old_path, path,session):
        if path[-1] !='/':
            path=path+'/'
        if old_path[-1] !='/':
            old_path=old_path+'/'
        if self.dir_exists(old_path,session):
            dir=self.getDirfromPath(old_path,session)
            dir.name=path
            session.add(dir)
            session.commit()
        else:
            print('directory does not exist')
        
    def  rename_file(self,old_path, path,session):
        if self.file_exists(old_path,session):
            file=self.getFilefromPath(old_path,session)
            file.name=path
            session.add(file)
            session.commit()
        else:
            print('file does not exist')
    
    def _findpathparent(self,path):
        if path=='':
            path='/'
        if path[-1]=='/':
            ending=path.rsplit('/', 2)[-2]
            return path[0:-len(ending)-1]
        else:
            ending=path.rsplit('/', 1)[-2]
            return ending+'/'
    
    def  save_file(self,path, content,session):
        if self.file_exists(path,session):
            file=self.getFilefromPath(path,session)
            #session.add(file)
            #session.flush()
            self._saverawfile(file.savedName,content)
        else:
            #print self._findpathparent(path)
            dir=self.getDirfromPath(self._findpathparent(path),session)
            file=File(name=path,savedName='virtual',author=self.user.name,directory_id=dir.id,owner_id=self.user.id)
            session.add(file)
            session.commit()
            file=session.query(File).filter(File.name==path,File.owner_id==self.user.id).first()
            id=file.id
            file.savedName='virtual'+str(id)
            session.add(file)
            session.commit()
            self._saverawfile(file.savedName,content)
            


    def _saverawfile(self,name,content):
        try:
            f=open(self.repos+name,'wb')
            f.write(writes_base64(content))
            f.close()
        except Exception as e:
            print e
    
    def _readrawfile(self,name):
        try:
            f=open(self.repos+name,'rb')
            return f.read()
            f.close()
        except Exception as  e:
            print e
        
    
    def get_file(self,path, session, content=False):
        if self.file_exists(path,session):
            file=session.query(File).filter(File.name==path,File.owner_id==self.user.id).first()
            record=file
            if content==True:
                record.content=self._readrawfile(file.savedName)
            return record
        else:
            print 'File does not exist'
    
    def get_directory(self,path, content,session):
        if path=='':
            path='/'
        if path[-1] !='/':
            path=path+'/'
        query=session.query(Directory).filter(Directory.name==path).filter(Directory.owner_id==self.user.id).first()
        return query        
        
    def create_directory(self,path,session):
        if path=='':
            path='/'
        if path[-1] !='/':
            path=path+'/'
        try:        
            if self.dir_exists(path,session):
                print 'Directory already exists'
                raise Exception
            #print self._findpathparent(path)
            dir=self.getDirfromPath(self._findpathparent(path),session)
            newdir=Directory(name=path,parent_id=dir.id,owner_id=self.user.id)
            session.add(newdir)
        except Exception as e:
            print e
    
       
#---------- single use functions
def initialize():
    engine=create_engine(config.dburl,echo=True)
    Base.metadata.create_all(engine)
    Session=session_factory()
    um=userManager()
    with session_scope() as session:
		usr=um.addUser('all','all','admin',session)   
		fm=fileManager(usr)
		fm.createRoot(session)   

def deleteAll():
    engine=create_engine(config.dburl,echo=True)
    Base.metadata.drop_all(engine)
                
def addUser1():
    Session=session_factory()
    um=userManager()
    with session_scope() as session:    
		usr=um.addUser('rdi','rdi','admin',session)
		fm=fileManager(usr)
		fm.createRoot(session)
    

#fm=fileManager()
