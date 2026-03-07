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
    Registering the metadata of document with filename, matter(namespace),
    child ids, parent ids, uploaded time and status.
    :param document_metadata:
    :return: str
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
    To retrieve a specific document from the MongoDB
    :param filename:
    :param matter:
    :return: dict
    """
    try:
        collection = get_registry()
        document_metadata = collection.find_one({"matter":matter,"filename":filename})
        if document_metadata is None:
            logger.error("Cound not find the document metadata you are asking for")
            raise RuntimeError("Cound not find the document metadata you are asking for")

        logger.info("Got the document metadata you are asking for.")
        return document_metadata
    except Exception as e:
        logger.exception(f"Error while getting document metadata,{e}")
        raise

def delete_document(filename: str, matter: str) -> str:
    """
    To delete a specific document metadata
    :param filename:
    :param matter:
    :return: str
    """
    try:
        collection = get_registry()
        result = collection.delete_one({"matter": matter, "filename": filename})
        if result.deleted_count == 0:
            logger.warning("Cound not find the document metadata you asked to delete")
            return "Cound not find the document metadata you are asking for"

        logger.info("Deleted the document metadata you asked for.")
        return "Deleted the document metadata you asked for."
    except Exception as e:
        logger.exception(f"Got an error while deleting the document metadata,{e}")
        raise RuntimeError("Got an error while deleting the document metadata")

def update_status(filename: str, matter: str, status: str) -> str:
    """
    Updating the status of the document metadata
    :param filename:
    :param matter:
    :param status:
    :return: str
    """
    try:
        collection = get_registry()
        query_filter = {'filename':filename,'matter':matter}
        update_operation = {'$set':{'status': status}}

        result = collection.update_one(query_filter, update_operation)
        if result.modified_count == 0:
            logger.warning("Cound not update the status of document metadata you asked for")
            return "Cound not update the status of document metadata you asked for"

        logger.info("Updated the status of the document metadata you asked for.")
        return "Updated the status of document metadata you asked for."
    except Exception as e:
        logger.exception(f"Got an error while updating status of the document metadata,{e}")
        raise RuntimeError("Got an error while updating status of the document metadata")