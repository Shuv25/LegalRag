"""
Creating the connection for mongodb to store all the parent docs and a registry
"""

import os
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

#-------Imports from other packages---------
from logs.logger import get_logger


logger = get_logger()
load_dotenv()

uri = os.getenv("MONGODB_URI")
mongo_db_name = os.getenv("MONGODB_DB_NAME")

_client: MongoClient | None = None
_database: Database | None = None

#--------Utility Functions-----------

def connect() -> None:
    """
    Initializes the MongoClient and pings the server to confirm connection.
    Should be called once during app lifespan startup.
    :return: None
    """
    global _client

    if _client is None:
        _client = MongoClient(uri, server_api=ServerApi(version='1', strict=True, deprecation_errors=True))
    try:
        _client.admin.command({'ping':1})
        logger.info("Successfully connected to MongoClient!")
    except Exception as e:
        logger.error(f"While connecting MongoClient, got an error: {e}")
        raise RuntimeError("Failed to connect to MongoDB")

def disconnect() -> None:
    """
    Closes the MongoClient connection.
    Should be called once during app lifespan shutdown.
    :return: None
    """
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoClient Disconnected")

def get_db() -> Database:
    """
    Returns the MongoDB database object.
    :return: pymongo.database.Database
    """
    global _database
    if _client is None:
        logger.error("MongoDB client is not connected.")
        raise RuntimeError("MongoDB client is not connected. Call connect() first.")
    if _database is None:
        _database = _client[mongo_db_name]
    return _database

def get_parents() -> Collection:
    """
    Returns the parent_chunks collection.
    :return: pymongo.collection.Collection
    """
    return get_db()["parent_chunks"]


def get_registry() -> Collection:
    """
    Returns the doc_registry collection.
    :return: pymongo.collection.Collection
    """
    return get_db()["doc_registry"]

def get_user_cred() -> Collection:
    """
    Returns the user_cred collection
    :return: pymongo.collection.Collection
    """
    return get_db()["user_cred"]