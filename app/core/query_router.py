"""
Adaptive query router for legal RAG pipeline.
Uses a LangChain agent with retrieval tool and MongoDB checkpointer
to classify, retrieve and generate legal answers with memory.
"""
from langchain.agents import create_agent

#-----------Imports from other packages------------
from logs.logger import get_logger
from app.common.llm import generator_llm
from app.core.retrieval_type import make_retrieval_tool
from app.utils.checkpointer import get_checkpointer
from evaluation.mlflow_logger import load_prompt_from_registry

logger = get_logger()

def route_query(query: str, matter: str, session_id: str) -> str:
    """
    Routes query through agent with memory, retrieval tool and generation.
    :param query: user's legal question
    :param matter: Pinecone namespace
    :param session_id: unique session identifier for memory
    :return: generated answer string
    """
    try:
        agent_prompt = load_prompt_from_registry("agent_prompt", version=2)
        retrieve_tool = make_retrieval_tool(matter)
        checkpointer = get_checkpointer()

        agent = create_agent(
            model=generator_llm,
            tools=[retrieve_tool],
            system_prompt=agent_prompt,
            checkpointer=checkpointer
        )

        config = {"configurable": {"thread_id": session_id}}
        result = agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=config
        )
        logger.info(f"\nResult:{result}\n")
        response = result["messages"][-1].content
        logger.info(f"Agent response generated for session: {session_id}")
        return response

    except Exception as e:
        logger.error(f"Route query failed: {e}")
        raise RuntimeError(f"Route query failed: {e}")