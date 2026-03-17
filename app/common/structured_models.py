"""
Pydantic models for structured LLM outputs.
Used across the pipeline for type-safe LLM responses.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional

class QueryType(BaseModel):
    retrieval: Literal['LOOKUP', 'ANALYTICAL', 'COMPARATIVE','GENERAL'] = Field(
        ...,
        description=(
            "Classify the legal query into one of three types:\n"
            "- LOOKUP: exact term or clause lookup ('what is clause 4.2', 'define indemnification')\n"
            "- ANALYTICAL: requires reasoning over document ('what are payment terms', 'summarize obligations')\n"
            "- COMPARATIVE: comparing across multiple documents ('compare Apple vs Microsoft IP clauses')"
            "- GENERAL: greetings, small talk, or non-legal questions ('hi', 'how are you', 'what is photosynthesis')"
        )
    )

class QueryModel(BaseModel):
    query: str = Field(..., description="Enter the query")
    matter: str = Field(..., description="Enter thr matter")
    session_id: Optional[str] = None

class RetrievalResponse(BaseModel):
    message: str
    session_id: str