"""
Document indexing pipeline for legal PDFs.
Orchestrates the full ingestion flow: loading, chunking, embedding,
and storing parent chunks in MongoDB and child chunks in Pinecone.
"""

from datetime import datetime, timezone
from typing import BinaryIO

#---------Import from other packages----------
from logs.logger import get_logger
from app.utils.registry import get_document, register_document, update_chunk_ids, update_status
from app.utils.embeddings import embed
from app.ingestion.loader import load_pdf
from app.ingestion.chunker import chunk_document
from app.utils.pinecone_vdb import get_index
from app.utils.mongo import get_parents

logger = get_logger()

def pinecone_upsertion(child_embeddings: list[list[float]], matter: str, child_chunks: list) -> list:
    """
    Embeds and upserts child chunks into Pinecone under the given namespace.
    :param child_embeddings: list of embedding vectors for each child chunk
    :param matter: client matter used as Pinecone namespace
    :param child_chunks: list of child chunk dicts containing child_id and metadata
    :return: list of child chunk IDs
    """
    try:
        index = get_index()
        vectors = []
        for embeddings, chunk in zip(child_embeddings,child_chunks):
            key = {
                "id":chunk["child_id"],
                "values":embeddings,
                "metadata":chunk["metadata"]
            }
            vectors.append(key)

        index.upsert(vectors,namespace=matter)
        logger.info("Successfully upserted the vectors inside the pinecone index")
        child_ids = [chunk["child_id"] for chunk in child_chunks]
        return child_ids

    except Exception as e:
        logger.error(f"Got some error while upserting vectors inside the pinecone index:{e}")
        raise RuntimeError("Got some error while upserting vectors inside the pinecone index")

def mongo_upsertion(parent_chunks: list):
    """
    Inserts parent chunks into MongoDB parent_chunks collection.
    :param parent_chunks: list of parent chunk dicts containing parent_id and text
    :return: list of parent chunk IDs
    """
    try:
        collection = get_parents()
        collection.insert_many(parent_chunks)
        parent_ids = [chunk["parent_id"] for chunk in parent_chunks]
        return parent_ids
    except Exception as e:
        logger.error(f"Got some error while upserting parent data inside the mongodb:{e}")
        raise RuntimeError("Got some error while upserting parent data inside the mongodb")

def index_document(filename: str, matter: str, file: BinaryIO):
    """
    Main entry point for the ingestion pipeline.
    Checks for duplicates, loads and chunks the PDF, embeds child chunks,
    stores parents in MongoDB and children in Pinecone, then updates the registry.
    :param filename: name of the PDF file
    :param matter: client matter / Pinecone namespace
    :param file: binary file stream from UploadFile.file
    :return: dict with status and message
    """
    try:
        get_document(filename, matter)
        logger.info(f"{filename} already exists for matter {matter}")
        return {
            "status": "duplicate",
            "message": "Document already present. Upload a different document."
        }

    except ValueError:
        try:
            logger.info("Document not found in registry. Proceeding with indexing.")

            documents = load_pdf(file)
            parent_chunks, child_chunks, chunk_config = chunk_document(documents, filename, matter)

            register_document({
                "filename": filename,
                "matter": matter,
                "child_ids": [],
                "parent_ids": [],
                "chunk_config": chunk_config,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "status": "ingesting"
            })

            child_embeddings = embed([chunk["text"] for chunk in child_chunks])
            child_ids = pinecone_upsertion(child_embeddings, matter, child_chunks)
            parent_ids = mongo_upsertion(parent_chunks)

            update_chunk_ids(filename, matter, child_ids, parent_ids)
            update_status(filename, matter, "active")

            logger.info(f"Successfully indexed {filename} for matter {matter}")
            return {
                "status": "success",
                "message": f"{filename} indexed successfully"
            }

        except Exception as e:
            update_status(filename, matter, "failed")
            logger.error(f"Error while indexing document: {e}")
            raise RuntimeError("Got some error while indexing document")

