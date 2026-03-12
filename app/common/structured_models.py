"""
Pydantic models for structured LLM outputs.
Used across the pipeline for type-safe LLM responses.
"""

from pydantic import BaseModel, Field
from typing import Literal

class QueryType(BaseModel):
    retrieval: Literal['LOOKUP', 'ANALYTICAL', 'COMPARATIVE'] = Field(
        ...,
        description=(
            "Classify the legal query into one of three types:\n"
            "- LOOKUP: exact term or clause lookup ('what is clause 4.2', 'define indemnification')\n"
            "- ANALYTICAL: requires reasoning over document ('what are payment terms', 'summarize obligations')\n"
            "- COMPARATIVE: comparing across multiple documents ('compare Apple vs Microsoft IP clauses')"
        )
    )

class QueryModel(BaseModel):
    query: str = Field(..., description="Enter the query")
    matter: str = Field(..., description="Enter thr matter")