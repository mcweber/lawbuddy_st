# ---------------------------------------------------
# Version: 06.03.2025
# Author: M. Weber
# ---------------------------------------------------
# 17.12.2024 deactivated SSL verification
# ---------------------------------------------------

from datetime import datetime
import os
from dotenv import load_dotenv

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# Define constants ----------------------------------
load_dotenv()

mongoClient = MongoClient(
    os.environ.get('MONGO_URI_PRIVAT_01'),
    tls=True,
    tlsAllowInvalidCertificates=True
)
database = mongoClient.law_buddy
collection = database.config

# Systemprompt Functions -----------------------------------------

def update_systemprompt(text: str = ""):
    result = collection.update_one({"key": "systemprompt"}, {"$set": {"content": text}})

def get_systemprompt() -> str:
    result = collection.find_one({"key": "systemprompt"})
    return str(result.get("content"))
