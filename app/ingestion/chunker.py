"""
Document chunker for legal PDFs.
Dynamically computes parent and child chunk sizes based on
word distribution analysis, then splits documents into
parent chunks (for LLM context) and child chunks (for vector retrieval).
"""

from uuid import uuid4
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter

#-----------Imports from other packages------------

from logs.logger import get_logger

logger = get_logger()


def analyze_chunk_sizes(word_counts: list[int]) -> dict:
    """
    Helper function to compute parent and child chunk sizes.

    Steps:
    - analyze word distribution
    - adjust using variance
    - convert words → tokens
    - derive parent/child chunk sizes
    :param word_counts: list containing  word counts of each page
    """

    arr = np.array(word_counts)

    mean = arr.mean()
    std = arr.std()

    p50 = np.percentile(arr, 50)
    p75 = np.percentile(arr, 75)

    variance_ratio = std / mean if mean else 0

    # choose base document size
    base_words = p50 if variance_ratio > 0.7 else p75

    # convert words to tokens (1 word is 0.7 token so 1 token is 1.33 word)
    tokens = base_words * 1.33

    # parent chunk (larger context)
    parent_chunk = int(tokens * 0.35)
    parent_overlap = int(parent_chunk * 0.15)

    parent_chunk = max(parent_chunk, 800)

    # child chunk (retrieval unit)
    child_chunk = int(parent_chunk * 0.40)
    child_overlap = int(child_chunk * 0.20)

    child_chunk = max(child_chunk, 250)

    token_to_char = 4

    parent_chunk = parent_chunk * token_to_char
    parent_overlap = parent_overlap * token_to_char
    child_chunk = child_chunk * token_to_char
    child_overlap = child_overlap * token_to_char

    return {
        "parent_chunk": parent_chunk,
        "parent_overlap": parent_overlap,
        "child_chunk": child_chunk,
        "child_overlap": child_overlap
    }

def split_into_chunks(
        documents: list[dict],
        parent_splitter: RecursiveCharacterTextSplitter,
        child_splitter: RecursiveCharacterTextSplitter,
        filename: str,
        matter: str
) -> tuple[list,list] | None:
    """
        Splits documents into parent and child chunks using provided splitters.
        Each child chunk maintains a reference to its parent via parent_id,
        preserving page number and metadata for downstream retrieval.
        :param documents:  list of page dicts from loader.py
        :param parent_splitter: recursive character text splitter for parent
        :param child_splitter: recursive character text splitter for child
        :param filename: original PDF filename
        :param matter: client matter / Pinecone namespace
        :return: tuple of (parent_docs, child_docs) or None if no content
    """

    parent_docs = []
    child_docs = []
    all_parent_chunks = []
    for doc in documents:
        if doc["page_content"]:
            parent_chunks = parent_splitter.split_text(doc["page_content"])
            for chunk in parent_chunks:
                parent_id = str(uuid4())
                all_parent_chunks.append((parent_id,chunk,doc['page_no']))
                parent_indexes = {
                    "parent_id": parent_id,
                    "text": chunk,
                    "metadata": {
                        "filename": filename,
                        "matter": matter,
                        "page_no": doc["page_no"]
                    }
                }
                parent_docs.append(parent_indexes)

    for parent_id, parent_chunk, page_no in all_parent_chunks:
        child_chunks = child_splitter.split_text(parent_chunk)
        for chunk in child_chunks:
            child_indexes = {
                        "child_id": str(uuid4()),
                        "parent_id": parent_id,
                        "text": chunk,
                        "metadata": {
                            "filename": filename,
                            "matter": matter,
                            "page_no": page_no,
                            "parent_id": parent_id
                        }
                    }
            child_docs.append(child_indexes)

    logger.info(f"Created {len(parent_docs)} parent chunks")
    logger.info(f"Created {len(child_docs)} child chunks")

    return parent_docs, child_docs

def chunk_document(documents: list[dict], filename: str, matter: str) -> tuple[list,list] | None:
    """
    Main entry point for chunking a document.
    Analyzes word distribution, computes optimal chunk sizes,
    and returns parent and child chunks with metadata.
    :param documents: list of page dicts from loader.py
    :param filename: original PDF filename
    :param matter: client matter / Pinecone namespace
    :return: tuple of (parent_docs, child_docs) or None if no content
    """
    try:
        word_counts = [
            len(doc["page_content"].split())
            for doc in documents
            if doc.get("page_content")
        ]

        if not word_counts:
            logger.warning(f"No valid content found in {filename}")
            return None

        chunk_config = analyze_chunk_sizes(word_counts)

        logger.info(
            f"{filename} | parent_chunk={chunk_config['parent_chunk']}, "
            f"parent_overlap={chunk_config['parent_overlap']}, "
            f"child_chunk={chunk_config['child_chunk']}, "
            f"child_overlap={chunk_config['child_overlap']}"
        )

        parent_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=chunk_config['parent_chunk'],
                            chunk_overlap=chunk_config['parent_overlap'],
                            )

        child_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=chunk_config['child_chunk'],
                            chunk_overlap=chunk_config['child_overlap'],
                            )

        return split_into_chunks(
                                documents,
                                parent_splitter,
                                child_splitter,
                                filename,
                                matter)

    except Exception as e:
        logger.error(f"Error while chunking document: {e}")
        raise RuntimeError("Error while chunking document")

