"""
Creating the connection and initializing index for storing the child chunks inside the pinecone vector database
"""

import os
from dotenv import load_dotenv
from typing import Any
from pinecone import Pinecone, ServerlessSpec

#-------Imports from other packages---------
from logs.logger import get_logger

load_dotenv()
logger = get_logger()

pinecone_api_key = os.getenv("PINECONE_API_KEY")

_pc: Pinecone | None = None
_index = None
_index_name: str | None = None

#--------Utility Functions-----------

def connect(index_name: str) -> None:
    """
    Initialized the pinecone client
    :param index_name: name of the index inside the pinecone
    :return: None
    """
    global _pc, _index_name
    try:
        if _pc is None:
            _pc = Pinecone(api_key=pinecone_api_key)
            logger.info("Pinecone vector db is connected")

        _index_name = index_name

        if not _pc.has_index(_index_name):
            _pc.create_index(
                name=_index_name,
                vector_type="dense",
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            logger.info(f"Pinecone index '{_index_name}' created")
    except Exception as e:
        logger.error(f"Got some error while connecing to pinecone index:{e}")
        raise RuntimeError("Got some error while connecing to pinecone index")

def get_index() -> Any:
    """
    Initialized the pinecone _index
    :return: Index
    """
    global _index

    if _pc is None:
        logger.error("Pinecone client is not connected")
        raise RuntimeError("Pinecone client is not connected. Call connect() first.")
    if _index is None:
        _index = _pc.Index(_index_name)
        logger.info(f"{_index_name} index is initialized")

    return _index