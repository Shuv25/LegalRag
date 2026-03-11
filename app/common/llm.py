"""
LLM client initialization for the legal RAG pipeline.
Initializes Groq LLM instances for routing and generation.
"""

import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

router_llm = ChatGroq(
    model = os.getenv("ROUTER_LLM"),
    api_key = os.getenv("GROQ_API_KEY"),
    temperature= 0.3
)

generator_llm = ChatGroq(
    model=os.getenv("GENERATOR_LLM"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1
)
