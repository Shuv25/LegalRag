"""
Registry utility for managing document metadata in MongoDB.
Tracks child and parent chunk IDs for each ingested document,
enabling clean deletion and status management across Pinecone and MongoDB.
"""

#-------Imports from other packages---------
from logs.logger import get_logger
from app.utils.mongo import get_registry

logger = get_logger()

#---------Utility Functions---------

def register_document(document_metadata: dict) -> None:
    """
    Registers a new document's metadata in the registry collection.
    Called at the start of ingestion with status set to 'ingesting'.
    :param document_metadata: dict containing filename, matter, child_ids,
                              parent_ids, uploaded_at and status
    :return: None
    """
    try:
        collection = get_registry()
        collection.insert_one(document_metadata)
        logger.info("Registered your document metadata")
    except Exception as e:
        logger.error(f"Encountered some error while registering document metadata:{e}")
        raise RuntimeError("Encountered some error while registering document metadata")

def get_document(filename: str, matter: str) -> dict:
    """
    Retrieves a document's metadata from the registry collection.
    Used for duplicate checks and fetching chunk IDs for deletion.
    :param filename: original PDF filename
    :param matter: client matter / Pinecone namespace
    :return: document metadata dict
    """
    try:
        collection = get_registry()
        document_metadata = collection.find_one({"matter":matter,"filename":filename}, {"_id": 0})
        if document_metadata is None:
            logger.error("Could not find the document metadata you are asking for")
            raise ValueError("Could not find the document metadata you are asking for")

        logger.info("Got the document metadata you are asking for.")
        return document_metadata
    except Exception as e:
        logger.exception(f"Error while getting document metadata,{e}")
        raise

def delete_document(filename: str, matter: str) -> str:
    """
    Deletes a document's metadata from the registry collection.
    Should be called after chunks are cleaned from Pinecone and MongoDB.
    :param filename: original PDF filename
    :param matter: client matter / Pinecone namespace
    :return: success or warning message
    """
    try:
        collection = get_registry()
        result = collection.delete_one({"matter": matter, "filename": filename})
        if result.deleted_count == 0:
            logger.warning("Could not find the document metadata you asked to delete")
            return "Could not find the document metadata you are asking for"

        logger.info("Deleted the document metadata you asked for.")
        return "Deleted the document metadata you asked for."
    except Exception as e:
        logger.exception(f"Got an error while deleting the document metadata,{e}")
        raise RuntimeError("Got an error while deleting the document metadata")

def update_status(filename: str, matter: str, status: str) -> dict:
    """
    Updates the ingestion status of a document in the registry.
    Valid statuses: 'ingesting', 'active', 'failed', 'inactive'.
    :param filename: original PDF filename
    :param matter: client matter / Pinecone namespace
    :param status: new status to set
    :return: success or warning message with bool value
    """
    try:
        collection = get_registry()
        query_filter = {'filename':filename,'matter':matter}
        update_operation = {'$set':{'status': status}}

        result = collection.update_one(query_filter, update_operation)
        if result.modified_count == 0:
            logger.warning("Could not update the status of document metadata you asked for")
            return {
                "updated": False,
                "message": "Could not update the status of document metadata you asked for"
            }

        logger.info("Updated the status of the document metadata you asked for.")
        return {
            "updated":True,
            "message":"Updated the status of document metadata you asked for."
        }
    except Exception as e:
        logger.exception(f"Got an error while updating status of the document metadata,{e}")
        raise RuntimeError("Got an error while updating status of the document metadata")

def update_chunk_ids(filename: str, matter: str, child_ids: list, parent_ids: list) -> dict:
    """
    Updates the child and parent chunk IDs of a registered document after successful indexing.
    :param filename: original PDF filename
    :param matter: client matter / Pinecone namespace
    :param child_ids: list of child chunk IDs stored in Pinecone
    :param parent_ids: list of parent chunk IDs stored in MongoDB
    :return: success or warning message with bool value
    """
    try:
        collection = get_registry()
        query_filter = {'filename':filename,'matter':matter}
        update_operation = {'$set':{'child_ids': child_ids,'parent_ids':parent_ids}}

        result = collection.update_one(query_filter, update_operation)
        if result.modified_count == 0:
            logger.warning("Could not update the child and parent ids of document metadata you asked for")
            return {
                "updated":False,
                "message":"Could not update the child and parent ids of document metadata you asked for"
            }

        logger.info("Updated the child and parent ids of the document metadata you asked for.")
        return {
            "updated":True,
            "message":"Updated the child and parent ids of document metadata you asked for."
        }
    except Exception as e:
        logger.exception(f"Got an error while updating child and parent ids of the document metadata,{e}")
        raise RuntimeError("Got an error while updating child and parent ids of the document metadata")