"""
Reranking utility for legal document retrieval.
Loads a CrossEncoder model once at startup and reranks
retrieved candidate documents by relevance to the user query.
"""

from sentence_transformers import CrossEncoder

#---------Imports from other packages----------
from logs.logger import  get_logger

logger = get_logger()

_rerank_model: CrossEncoder | None = None

def load_rerank_model() -> None :
    """
    Reranking utility for legal document retrieval.
    Loads a CrossEncoder model once at startup and reranks
    retrieved candidate documents by relevance to the user query.
    """
    global _rerank_model
    try:
        _rerank_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        logger.info("Rerank model is loaded")
    except Exception as e:
        logger.error(f"Error loading rerank model: {e}")
        raise RuntimeError("Error loading rerank model")

def rerank_docs(query:str, documents: list[dict], top_n: int = 3) -> list[dict]:
    """
    Reranks candidate documents against the user query using a CrossEncoder.
    :param query: user's legal question
    :param documents: list of candidate dicts containing text and metadata
    :param top_n: number of top documents to return after reranking
    :return: top N reranked document dicts
    """
    try:
        if _rerank_model is None:
            logger.error("Rerank model not loaded. Call load_rerank_model() first.")
            raise RuntimeError("Rerank model not loaded. Call load_rerank_model() first.")

        texts = [doc["text"] for doc in documents]
        pairs = [(query,text) for text in texts]
        scores = _rerank_model.predict(pairs)

        scored_docs = zip(scores,documents)
        sorted_docs = sorted(scored_docs, key=lambda x: x[0], reverse=True)
        return [doc for _, doc in sorted_docs[:top_n]]
    except Exception as e:
        logger.error("Got some error while reranking the retrieved docs")
        raise RuntimeError("Got some error while reranking the retrieved docs")