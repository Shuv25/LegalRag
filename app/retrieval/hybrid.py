"""
Hybrid retrieval module combining semantic vector search from Pinecone
and BM25 lexical ranking from MongoDB. Results are merged using
Reciprocal Rank Fusion (RRF) to produce final ranked parent documents.
"""
import mlflow
from rank_bm25 import BM25Okapi
from mlflow.entities import SpanType

#-------Imports from other packages---------
from logs.logger import get_logger
from app.utils.pinecone_vdb import get_index
from app.utils.embeddings import embed
from app.utils.mongo import get_parents

logger = get_logger()

@mlflow.trace(span_type=SpanType.RETRIEVER)
def semantic_search(query: str, matter: str, top_n: int = 10) -> list[dict]:
    """
    Perform semantic vector search in Pinecone.
    :param query: user query string
    :param matter: Pinecone namespace
    :param top_n: number of results to retrieve
    :return: list of matched child chunks
    """
    try:
        index = get_index()
        query_embedding = embed([query])[0]
        results = index.query(
            vector=query_embedding,
            top_k=top_n,
            namespace=matter,
            include_metadata=True,
            include_values=False,
        )
        if not results["matches"]:
            logger.warning(f"No documents found for query: {query}")
            raise ValueError(f"No documents found for query: {query}")

        logger.info("Fetched documents from Pinecone")
        return results["matches"]

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise RuntimeError("Semantic search failed")

@mlflow.trace(span_type=SpanType.RETRIEVER)
def bm25_search(query: str, matter: str, top_n: int = 10) -> list[dict]:
    """
    Perform BM25 ranking on ALL parent documents for a matter.
    :param query: user query string
    :param matter: client matter / Pinecone namespace
    :param top_n: number of documents to return
    :return: ranked parent documents
    """
    try:
        collection = get_parents()
        result = collection.find(
            {"metadata.matter": matter},
            {"text": 1, "parent_id": 1, "metadata": 1, "_id": 0}
        )
        docs = list(result)

        if not docs:
            logger.warning(f"No parent documents found for matter: {matter}")
            raise ValueError(f"No documents found for matter: {matter}")

        texts = [doc["text"] for doc in docs]
        tokenized_docs = [text.split() for text in texts]
        tokenized_query = query.split()

        bm25 = BM25Okapi(tokenized_docs)
        scores = bm25.get_scores(tokenized_query)

        ranked_docs = sorted(
            zip(docs, scores),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return [
            {
                "parent_id": doc["parent_id"],
                "text": doc["text"],
                "score": float(score),
                "metadata": doc.get("metadata", {})
            }
            for doc, score in ranked_docs
        ]

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"BM25 search failed: {e}")
        raise RuntimeError("BM25 search failed")


def reciprocal_rank_fusion(semantic_results: list[dict], bm25_results: list[dict], k: int = 60) -> list[dict]:
    """
    Merge semantic and BM25 rankings using RRF.
    :param semantic_results: semantic search results from Pinecone
    :param bm25_results: BM25 ranked results from MongoDB
    :param k: RRF constant (default 60)
    :return: fused ranked documents
    """
    try:
        fused_scores = {}
        seen_parents = set()

        for rank, doc in enumerate(semantic_results, start=1):
            parent_id = doc["metadata"].get("parent_id")
            if not parent_id or parent_id in seen_parents:
                continue
            seen_parents.add(parent_id)
            fused_scores[parent_id] = {"parent_id": parent_id, "score": 1 / (k + rank)}

        for rank, doc in enumerate(bm25_results, start=1):
            parent_id = doc["parent_id"]
            if parent_id not in fused_scores:
                fused_scores[parent_id] = {"parent_id": parent_id, "score": 0}
            fused_scores[parent_id]["score"] += 1 / (k + rank)
            fused_scores[parent_id]["text"] = doc["text"]

        ranked_results = sorted(
            [doc for doc in fused_scores.values() if "text" in doc],
            key=lambda x: x["score"],
            reverse=True
        )

        return ranked_results

    except Exception as e:
        logger.error(f"RRF failed: {e}")
        raise RuntimeError("RRF failed")

@mlflow.trace(span_type=SpanType.RETRIEVER)
def hybrid_search(query: str, matter: str, top_n: int = 5) -> list[dict]:
    """
    Run hybrid retrieval using semantic search + BM25 + RRF.
    :param query: user query string
    :param matter: Pinecone namespace
    :param top_n: number of final results to return
    :return: fused ranked parent documents
    """
    try:
        semantic_results = semantic_search(query, matter)
        bm25_results = bm25_search(query, matter)
        fused_results = reciprocal_rank_fusion(semantic_results, bm25_results)

        logger.info(f"Hybrid search completed, returning top {top_n} results")
        return fused_results[:top_n]

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise RuntimeError("Hybrid search failed")