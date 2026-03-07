"""
Creating the connection and initializing index for storing the child chunks inside the pinecone
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone
from pinecone.pinecone import Index

#-------Imports from other packages---------
from logs.logger import get_logger

load_dotenv()
logger = get_logger()

pinecone_api_key = os.getenv("PINECONE_API_KEY")

_pc: Pinecone | None = None
_index: Index | None = None

#--------Utility Functions-----------

def connect() -> None:
    """
    Initialized the pinecone client
    :return: Pinecone
    """
    global _pc
    if _pc is None:
        _pc = Pinecone(api_key=pinecone_api_key)
        logger.info("Pinecone vector db is connected")

def get_index(index_name: str) -> Index:
    """
    Initialized the pinecone index
    :param index_name:
    :return: Index
    """
    global _index

    if _pc is None:
        logger.error("Pinecone client is not connected")
        raise RuntimeError("Pinecone client is not connected. Call connect() first.")
    if _index is None:
        _index = _pc.Index(index_name)
        logger.info(f"{index_name} index is initialized")

    return _index