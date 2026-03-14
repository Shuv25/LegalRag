"""
LLM response generator for legal RAG pipeline.
Takes retrieved parent documents and user query to generate
accurate, grounded legal answers using Groq LLM.
"""
import mlflow
from mlflow.entities import SpanType

#-----------Imports from other packages------------
from logs.logger import get_logger
from app.common.llm import generator_llm
from evaluation.mlflow_logger import load_prompt_from_registry

logger = get_logger()

def format_context(documents: list[dict]) -> str:
    """
    Formats retrieved parent documents into a single context string for the LLM.
    :param documents: list of parent document dicts with text and metadata
    :return: formatted context string
    """
    context_parts = []
    for i, doc in enumerate(documents, start=1):
        filename = doc.get("metadata", {}).get("filename", "Unknown")
        page_no = doc.get("metadata", {}).get("page_no", "Unknown")
        text = doc.get("text", "")
        context_parts.append(
            f"[Document {i} | File: {filename} | Page: {page_no}]\n{text}"
        )
    return "\n\n".join(context_parts)

@mlflow.trace(span_type=SpanType.LLM)
def generate(query: str, documents: list[dict]) -> str:
    """
    Generates a legal answer using retrieved context and user query.
    :param query: user's legal question
    :param documents: list of retrieved parent document dicts
    :return: generated answer string
    """
    try:
        GENERATOR_PROMPT = load_prompt_from_registry("generator_prompt", version=5)
        GENERAL_PROMPT = load_prompt_from_registry("general_prompt", version=5)
        if not documents:
            prompt = GENERAL_PROMPT.format(query=query)
        else:
            context = format_context(documents)
            prompt = GENERATOR_PROMPT.format(query=query, context=context)

        response = generator_llm.invoke(prompt)
        logger.info("Successfully generated response")
        return response.content

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise RuntimeError("Generation failed")