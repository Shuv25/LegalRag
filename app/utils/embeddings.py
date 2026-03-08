"""
Embedding utility for encoding text chunks.
Loads the all-MiniLM-L6-v2 model once at startup and exposes
an embed() function for encoding text into dense vectors.
"""

from sentence_transformers import SentenceTransformer

#---------Imports from other packages----------
from logs.logger import  get_logger

logger = get_logger()

_model: SentenceTransformer | None = None

def load_model() -> None:
    """
    To load the embedding model
    :return: None
    """
    global _model
    try:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Embedding model loaded!")
    except Exception as e:
        logger.error(f"Error loading embedding model: {e}")
        raise RuntimeError("Error loading embedding model")

def embed(texts: list[str]) -> list[list[float]]:
    """
    To encode the docs into vectors
    :param texts: documents
    :return: multi dimensional vectors
    """
    if _model is None:
        logger.error("Model not loaded. Call load_model() first.")
        raise RuntimeError("Model not loaded. Call load_model() first.")
    return _model.encode(texts).tolist()