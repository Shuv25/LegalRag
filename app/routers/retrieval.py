"""
Retrieval router for legal document querying.
Accepts user queries and routes them through the adaptive
retrieval pipeline to generate grounded legal answers.
"""
import mlflow
from uuid import uuid4
from mlflow.entities import SpanType
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

#----------Import from other packages----------
from logs.logger import get_logger
from app.common.structured_models import QueryModel, RetrievalResponse
from app.core.query_router import route_query

logger = get_logger()
limiter = Limiter(key_func=get_remote_address)
retrieval_router = APIRouter()

@retrieval_router.post("/query", tags=["Retrieval"])
@limiter.limit("30/minute")
@mlflow.trace(span_type=SpanType.CHAIN)
def query_documents(request: Request, input: QueryModel) -> RetrievalResponse:
    """
    Queries the legal RAG pipeline with a user question.
    Creates new session if session_id not provided.
    :param input: QueryModel containing query, matter and optional session_id
    :return: generated answer and session_id
    """
    try:
        query = input.query
        matter = input.matter
        session_id = input.session_id or str(uuid4())

        response = route_query(query, matter, session_id)
        if not response:
            logger.error("No response found")
            raise ValueError("No response found")

        return RetrievalResponse(
            message=response,
            session_id=session_id
        )

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Got some error while returning response: {e}")
        raise RuntimeError("Got some error while returning response")