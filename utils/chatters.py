import os, sys, re
from twitchio.ext import commands
from ansimarkup import ansiprint as print
from pymongo import MongoClient
import motor.motor_asyncio
import urllib
import json
import simpleobsws
import random
import glob
from tinydb import TinyDB, Query 

CHATTERS_JSON = os.path.join(os.path.abspath(os.path.curdir), "chatters.json")


###  chatter.db:
###  tables -> chatters: |user_id|twitch_uid|twitch_username|nickname|location|pronouns|pronunciation|
###            user_attr: |user_id|
###            fave_animals: |animal_id| animal_name| gwb_rating|
###            stonks
###  trading table:
###  

class UserDB:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017/")
        self.db = self.client.get_database("streamDB")
        self.collection = self.db["userInfo"]

    async def add_doc_to_db(self, doc):
        await self.collection.insert_one(doc)
        return

    async def add_user_to_db(self, name):
        user = await self.collection.find_one({'username': name})
        if user is not None and user.get('username'):
            print("Error: user is already in database")
            return

        document = {
            'username': name
        }
        await self.collection.insert_one(document)
        return

    async def addtouser(self, name, attribute, value):
        document = {
            attribute: value
        }

        result = await self.collection.update_one({'username': name }, { '$set': document})
        if result.modified_count == 0:
            print(f"Could not update document for user {name}")
        
        print(f'Updated document: {result.modified_count}')
        return

    async def getAllUsers(self):
        cur = self.collection.find({}, {'username': 1, '_id': 0}) # Don't await!!! this gets a cursor
        userlist = []
        async for document in cur:
            userlist.append(document.get('username'))
        return userlist

    async def getUserAttr(self, name, attribute):
        result = await self.collection.find_one({'username': name}, {f'{attribute}': 1, '_id': 0})
        return result.get(attribute)

    async def getUser(self, name):
        result = await self.collection.find_one({'username': name}, {'_id': 0})
        return result



class Users:
    def __init__(self, username):
        self.query = Query()
        self.db = TinyDB(CHATTERS_JSON, indent=4)
        self.table = self.db.table("Users")
        response = self.check_db_for_user(username)
        if not response:
            self.user = username
            # private variable?
            self.attributes = {
                               'nickname': None,
                               'birthday': None,
                               'credit_card': None,
                               'stonks': None,
                               'pronouns': None,
                               'pronunciation': None,
                               'location': None,
                               'favorite_animal': None,
                               'age': None,
                               'club_penguin': None, 
                               'runescape': None,
                               'social_security_number': None
                               }
            # Nesting the attributes was annoying with TinyDB to update attributes so thank you @spongebob! 
            self._json_obj = { "username": self.user, **self.attributes } 
            # TODO: Can we make everything in the attr dict a separate attr
            # so that a user can call !girlwithbox.nickname 
            # <user>.<attr> without explicitly naming all the attributes    
            self.write_user()
        else:
            self._json_obj, self.user, self.attributes = response
        
        for attr, arg in self.attributes.items():
            setattr(self, attr, arg)   

    @classmethod
    def print_user_list(cls):
        userlist = []
        with open(CHATTERS_JSON) as chat:
            chatdb = json.load(chat)

        chatdb = chatdb['Users']
        for key in chatdb.keys():
            userlist.append(chatdb[key]["username"])
        return userlist
    
    def check_db_for_user(self, username):
        matches = self.table.search(self.query.username == username.lower())
       
        if len(matches) > 1:
            print(f"Found more than one {username}; returning first match")
            #raise Exception(f"More than one match found for {username}")
            user_dict = matches[0].copy()
            user = user_dict["username"]
            user_dict.pop("username")
            attributes = user_dict

        elif len(matches) == 0:
            return None
        else:
            user_dict = matches[0].copy()
            user = user_dict["username"]
            user_dict.pop("username")
            attributes = user_dict

        return {'username': user, **attributes}, user, attributes

    def set(self, attr, arg):
        # The json object that holds self.attributes
        # will it change if we change those attr?
        # Pointer or copy? Do we also need to update self._json_obj. Moot q since we expanded it
        self.attributes[attr] = arg
        self._json_obj[attr] = arg

        # create an attribute for the user so we can do !<user>.name
        setattr(self, attr, arg)
        # TODO: implement checks for certain attributes?
        self.write_user()
        return

    def write_user(self):
        if self.table.contains(self.query.username ==  self.user):
            self.table.update(self._json_obj, self.query.username == self.user)
        else:
            self.table.insert(self._json_obj)
        return

        #;;;;;;
        #;; 
        #;;;;;;
async def seed():
    db = UserDB()
    with open("chatters.json", 'r') as chatters:
        chatdb = json.load(chatters)
    users = chatdb['Users']
    for user in users.values():
        print(user)
        await db.add_doc_to_db(user)
    return


if __name__ == "__main__":
    db = UserDB()
    loop = db.client.get_io_loop()
    result = loop.run_until_complete(db.getUser('girlwithbox'))
    print(result)





