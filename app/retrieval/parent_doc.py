"""
Parent document fetcher for legal RAG pipeline.
Uses parent_ids from reranked child chunks to fetch
full parent documents from MongoDB for LLM context.
"""

#-------Imports from other packages---------
from logs.logger import get_logger
from app.utils.mongo import get_parents

logger = get_logger()


def fetch_parent_docs(reranked_docs: list[dict]) -> list[dict]:
    """
    Fetches full parent documents from MongoDB using parent_ids.
    :param reranked_docs: reranked documents containing parent_ids
    :return: list of full parent documents with text and metadata
    """
    try:
        if not reranked_docs:
            logger.warning("No reranked docs passed to parent fetcher")
            raise ValueError("No documents to fetch parents for")

        parent_ids = [doc["parent_id"] for doc in reranked_docs]

        collection = get_parents()
        results = collection.find(
            {"parent_id": {"$in": parent_ids}},
            {"_id": 0, "parent_id": 1, "text": 1, "metadata": 1}
        )

        docs = list(results)

        if not docs:
            logger.warning("No parent documents found in MongoDB")
            raise ValueError("No parent documents found")

        logger.info(f"Fetched {len(docs)} parent documents from MongoDB")
        return docs

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Parent document fetch failed: {e}")
        raise RuntimeError("Parent document fetch failed")