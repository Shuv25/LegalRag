"""
Retrieval router for legal document querying.
Accepts user queries and routes them through the adaptive
retrieval pipeline to generate grounded legal answers.
"""

from fastapi import APIRouter
from slowapi import  Limiter
from slowapi.util import get_remote_address

#----------Import from other packages----------
from logs.logger import get_logger
from app.common.structured_models import QueryModel
from app.core.query_router import route_query
from app.core.generator import generate

logger = get_logger()
limiter = Limiter(key_func=get_remote_address)
retrieval_router = APIRouter()

@retrieval_router.post("/query", tags=["Retrieval"])
@limiter.limit("30/minute")
def query_documents(input: QueryModel) -> str:
    """
    Queries the legal RAG pipeline with a user question.
    Routes through adaptive retrieval and generates a grounded answer.
    :param input: QueryModel containing query and matter
    :return: generated legal answer string
    """
    try:
        query = input.query
        matter = input.matter
        documents = route_query(query, matter)
        response = generate(query, documents)
        if not response:
            logger.error("No response found")
            raise ValueError("No response found")
        return response

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Got some error while returning response:{e}")
        raise RuntimeError("Got some error while returning response")