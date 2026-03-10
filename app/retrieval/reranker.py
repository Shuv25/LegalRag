"""
Reranking layer for retrieved hybrid search results.
Uses CrossEncoder to score and filter the most relevant
documents before passing to parent document fetcher.
"""

#-------Imports from other packages---------
from logs.logger import get_logger
from app.utils.rerank import rerank_docs

logger = get_logger()


def rerank_documents(query: str, documents: list[dict], top_n: int = 3) -> list[dict]:
    """
    Reranks hybrid search results using CrossEncoder.
    :param query: user query string
    :param documents: candidate documents from hybrid search
    :param top_n: number of top documents to return
    :return: top N reranked documents
    """
    try:
        if not documents:
            logger.warning("No documents passed to reranker")
            raise ValueError("No documents to rerank")

        reranked = rerank_docs(query, documents, top_n)
        logger.info(f"Reranked documents, returning top {top_n}")
        return reranked

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Reranking failed: {e}")
        raise RuntimeError("Reranking failed")