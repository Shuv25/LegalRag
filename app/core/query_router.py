"""
Adaptive query router for legal RAG pipeline.
Classifies incoming queries using an LLM and routes them
to the appropriate retrieval strategy.
"""
#-----------Imports from other packages------------
from logs.logger import get_logger
from app.common.llm import router_llm
from app.common.structured_models import QueryType
from app.core.retrieval_type import call_retrieval_type
from evaluation.mlflow_logger import load_prompt_from_registry

logger= get_logger()

def route_query(query: str, matter: str) -> list[dict]:
    """
    Main entry point for adaptive query routing.
    Classifies query using LLM and routes to correct retrieval strategy.
    :param query: user's legal question
    :param matter: Pinecone namespace
    :return: retrieved context string
    """
    try:
        ROUTER_PROMPT = load_prompt_from_registry("router_prompt", version=5)
        model_with_structure = router_llm.with_structured_output(QueryType)
        message = ROUTER_PROMPT.format(query=query)
        result = model_with_structure.invoke(message)
        retrieval_type = result.retrieval
        response = call_retrieval_type(retrieval_type, query, matter)
        return response
    except Exception as e:
        raise RuntimeError(f"Route query failed: {e}")
