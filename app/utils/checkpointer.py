"""
MongoDB checkpointer module for LangGraph state persistence.
Stores checkpoints in 'checkpointer' collection using shared MongoClient.
"""

import os
from dotenv import load_dotenv
from langgraph.checkpoint.mongodb import MongoDBSaver

#----------Import from other packages----------
from logs.logger import get_logger
from app.utils.mongo import get_checkpointer_collection, get_client

logger = get_logger()
load_dotenv()
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME"," ")

_checkpointer: MongoDBSaver | None = None

def load_checkpointer() -> MongoDBSaver:
    """
    Initializes and returns the shared MongoDBSaver checkpointer.
    :return: Initialized MongoDBSaver instance
    """
    try:
        global _checkpointer

        if _checkpointer is None:
            checkpointer_collection = get_checkpointer_collection()
            _checkpointer = MongoDBSaver(
                client=get_client(),
                collection = checkpointer_collection,
                db_name = MONGODB_DB_NAME,
            )
            logger.info("Checkpointer is being initialized")

        return _checkpointer

    except Exception as e:
        logger.error(f"Failed to initialize checkpointer: {e}")
        raise RuntimeError("Failed to initialize checkpointer")

def get_checkpointer() -> MongoDBSaver:
    """
    Returns the initialized checkpointer instance.
    :return: MongoDBSaver
    """
    if _checkpointer is None:
        raise RuntimeError("Checkpointer not initialized. Call load_checkpointer() first.")
    return _checkpointer
