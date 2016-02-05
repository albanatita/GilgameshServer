# -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 13:20:20 2016

@author: admin
"""
from sqlalchemy import select,func
from pgcontents.schema import users
from pgcontents.query import create_directory
import pgcontents.query as pgquery
from pgcontents.api_utils import to_api_path,split_api_filepath
from sqlalchemy import create_engine
from nbconvert import HTMLExporter
import nbformat
import HTMLParser
from pgcontents.api_utils import reads_base64

def usr_list(db):
    rows=db.execute(select({users.c.id}))
    return [row[0] for row in rows]

def usr_exists(db, user_id):
    """
    Internal implementation of dir_exists.
    Expects a db-style path name.
    """
    return db.execute(
        select(
            [func.count(users.c.id)],
        ).where(
            
                users.c.id == user_id,
        )
    ).scalar() != 0

def create_usr(db,user_id):
    db.execute(
        users.insert().values(
            id=user_id,
        )
    )
    create_directory(db,user_id,'//')
    create_directory(db,user_id,'//export')
    
def TreeFile(db,path):
    liste=pgquery.directories_in_directory(db, 'share', path)
    text='<ul>\n'
    for n in liste:
        text=text+'<li id='+n['name']+'>'+split_api_filepath(to_api_path(n['name']))[1]+'</li>\n'
        text2=TreeFile(db,n['name'])
        text=text+text2
    text=text+'</ul>\n'
    return text
    
#db=create_engine('postgresql://postgres:ishtar@localhost/ishtar')
##print usr_exists(db,'rdi')
##create_directory(db,'rdi','')
#print usr_list(db)
#create_usr(db,'share')
#print TreeFile(db,'/')
#db=create_engine('postgresql://postgres:ishtar@localhost/ishtar')
#fileContent=pgquery.get_file(db, "share", '/test.ipynb', include_content=True)
#db=create_engine('postgresql://postgres:ishtar@localhost/ishtar')
#
#fileContent=reads_base64(pgquery.get_file(db, "share",'/test.ipynb', include_content=True)['content'])
#print fileContent
##notebook= nbformat.reads(fileContent, as_version=4)
#notebook=fileContent
#db.dispose()
#html_exporter = HTMLExporter()
#html_exporter.template_file = 'basic'
#
#(body, resources) = html_exporter.from_notebook_node(notebook)