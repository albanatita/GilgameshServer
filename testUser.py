# -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 13:20:20 2016

@author: admin
"""
from sqlalchemy import select,func
from pgcontents.schema import users
from pgcontents.query import create_directory
from sqlalchemy import create_engine

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

    
    
db=create_engine('postgresql://postgres:ishtar@localhost/ishtar')
print usr_exists(db,'rdi')
create_directory(db,'rdi','')