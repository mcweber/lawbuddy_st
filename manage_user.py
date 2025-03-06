# ---------------------------------------------------
# Version: 06.03.2024
# Author: M. Weber
# ---------------------------------------------------
# ---------------------------------------------------

from datetime import datetime
import os
from dotenv import load_dotenv

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# Define constants ----------------------------------
load_dotenv()

mongoClient = MongoClient(os.environ.get('MONGO_URI_PRIVAT_01'))
database = mongoClient.law_buddy
collection = database.users

# User Functions -----------------------------------------

def add_user(user_name, user_pw) -> bool:
    try:
        collection.insert_one({
            'username': user_name,
            'user_password': user_pw,
            'created': datetime.now()
        })
        return True
    except DuplicateKeyError:
        return False
    

def check_user(user_name, user_pw) -> str:
    user = collection.find_one({
        'username': user_name,
        'user_password': user_pw
    })
    return user if user else ""


def delete_user(user_name) -> bool:
    collection.delete_one({'username': user_name})
    return True


def list_users() -> list:
    users = collection.find()
    return users
