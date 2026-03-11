"""
LLM response generator for legal RAG pipeline.
Takes retrieved parent documents and user query to generate
accurate, grounded legal answers using Groq LLM.
"""

#-----------Imports from other packages------------
from logs.logger import get_logger
from app.common.llm import generator_llm
from app.core.prompts import GENERATOR_PROMPT

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


def generate(query: str, documents: list[dict]) -> str:
    """
    Generates a legal answer using retrieved context and user query.
    :param query: user's legal question
    :param documents: list of retrieved parent document dicts
    :return: generated answer string
    """
    try:
        if not documents:
            logger.warning("No documents passed to generator")
            raise ValueError("No context documents provided for generation")

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