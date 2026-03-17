"""
Abstract base class and concrete implementations for retrieval routing.
Each retrieval type maps to a different search strategy in the pipeline.
"Add new retrieval types here using the @register_retrieval decorator."
"""
import json
from abc import ABC, abstractmethod
from langchain.tools import tool

#---------Imports from other packages
from logs.logger import get_logger
from app.retrieval.hybrid import bm25_search, hybrid_search
from app.retrieval.reranker import rerank_documents
from app.retrieval.parent_doc import fetch_parent_docs

logger = get_logger()

retrieval_type_registry: dict[str, type] = {}

def register_retrieval(name: str):
    def decorator(cls):
        key = name.lower()
        if key in retrieval_type_registry:
            raise ValueError(f"Retrieval type '{key}' already registered")
        retrieval_type_registry[key] = cls
        return cls
    return decorator

class RetrievalType(ABC):
    """
    Abstract base class for all retrieval strategies.
    All retrieval types must implement the route_to() method.
    """
    @abstractmethod
    def route_to(self, query: str, matter: str) -> list[dict]:
        pass

@register_retrieval("lookup")
class LookupRetrieval(RetrievalType):
    """BM25 only retrieval for exact legal term lookups."""
    def route_to(self, query: str, matter: str) -> list[dict]:
        return bm25_search(query, matter)

@register_retrieval("analytical")
class AnalyticalRetrieval(RetrievalType):
    """Hybrid search + reranker for analytical queries."""
    def route_to(self, query: str, matter: str) -> list[dict]:
        results = hybrid_search(query, matter)
        reranked = rerank_documents(query, results)
        return fetch_parent_docs(reranked)

@register_retrieval("comparative")
class ComparativeRetrieval(RetrievalType):
    """Multi-query + hybrid + reranker for comparative queries."""
    def route_to(self, query: str, matter: str) -> list[dict]:
        results = hybrid_search(query, matter)
        reranked = rerank_documents(query, results)
        return fetch_parent_docs(reranked)

@register_retrieval("general")
class GeneralRetrieval(RetrievalType):
    def route_to(self, query: str, matter: str) -> list[dict]:
        return []

def call_retrieval_type(retrieval_type: str, query: str, matter: str) -> list[dict]:
    """
    Looks up and executes the correct retrieval strategy.
    :param retrieval_type: retrieval type string
    :param query: user's legal question
    :param matter: Pinecone namespace
    :return: list of retrieved parent documents
    """
    try:
        retrieval_type_class = retrieval_type_registry.get(retrieval_type.lower())
        if retrieval_type_class:
            logger.info(f"RETRIEVAL TYPE: {retrieval_type}")
            retrieval_obj = retrieval_type_class()
            return retrieval_obj.route_to(query, matter)
        else:
            raise ValueError("Did not found any valid retrieval type")
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Got some error while doing retrieval: {e}")
        raise RuntimeError("Got some error while doing retrieval")

def make_retrieval_tool(matter: str):
    """
    Creates a LangChain retrieval tool bound to a specific matter.
    :param matter: Pinecone namespace
    :return: LangChain tool
    """
    @tool
    def retrieve_documents(retrieval_type: str, query: str) -> str:
        """
        Retrieves legal documents based on query classification.
        retrieval_type must be one of: lookup, analytical, comparative, general
        """
        results = call_retrieval_type(retrieval_type, query, matter)
        if not results:
            return "No documents found for this query."

        formatted = []
        for i, doc in enumerate(results, 1):
            filename = doc.get("metadata", {}).get("filename", "Unknown")
            page_no = doc.get("metadata", {}).get("page_no", "Unknown")
            text = doc.get("text", "")
            formatted.append(
                f"[Document {i} | File: {filename} | Page: {page_no}]\n{text}"
            )
        return "\n\n".join(formatted)
    return retrieve_documents