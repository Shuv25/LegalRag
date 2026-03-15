"""
Ingestion router for uploading and indexing legal PDF documents.
Provides endpoint for ingesting PDFs into Pinecone and MongoDB
via the document indexing pipeline.
"""

from typing import Annotated
from fastapi import APIRouter, Form, File, UploadFile, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

#----------Import from other packages----------
from logs.logger import get_logger
from app.ingestion.indexer import index_document

logger = get_logger()
limiter = Limiter(key_func=get_remote_address)
ingestion_router = APIRouter()

@ingestion_router.post("/upload", tags=["Ingestion"])
@limiter.limit("5/minute")
def data_insertion(
    request: Request,
    matter: str = Form(..., description="Client matter / Pinecone namespace"),
    file: Annotated[UploadFile, File(description="Legal PDF document to index")]  = ...
) -> dict:
    """
    Ingests a legal PDF document into the system.
    Loads, chunks, embeds and stores the document in Pinecone and MongoDB.
    :param matter: client matter used as Pinecone namespace
    :param file: uploaded PDF file
    :return: dict with status and message
    """
    try:
        logger.info(f"Ingestion request received for matter: {matter}")
        filename = file.filename
        return index_document(filename, matter, file.file)
    except Exception as e:
        logger.error(f"Got some error while using the insertion endpoint: {e}")
        raise



