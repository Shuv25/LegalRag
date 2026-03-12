"""
Document management router for retrieving and deleting legal documents.
Provides endpoints for fetching document metadata and removing documents
from the registry.
"""

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

#----------Import from other packages----------
from logs.logger import get_logger
from app.utils.registry import get_document, delete_document

logger = get_logger()
limiter = Limiter(key_func=get_remote_address)

document_router = APIRouter()

@document_router.get("/get_document", tags=["Documents"])
@limiter.limit("5/minute")
def find_document(request: Request,filename: str, matter: str) -> dict:
    """
    Retrieves metadata of a specific document from the registry.
    :param filename: name of the PDF file
    :param matter: client matter / Pinecone namespace
    :return: document metadata dict
    """
    try:
        logger.info(f"Document request received for matter: {matter}")
        return get_document(filename, matter)
    except Exception as e:
        logger.error(f"Got some error while using the get_document endpoint: {e}")
        raise

@document_router.delete("/delete_document", tags=["Documents"])
def remove_document(filename: str, matter: str) -> str:
    """
    Deletes a document's metadata from the registry.
    :param filename: name of the PDF file
    :param matter: client matter / Pinecone namespace
    :return: str with message
    """
    try:
        logger.info(f"Document delete received for matter: {matter}")
        return delete_document(filename, matter)
    except Exception as e:
        logger.error(f"Got some error while using the delete_document endpoint: {e}")
        raise
