"""
RAGAs evaluation pipeline for Legal RAG system.
Runs test queries through the pipeline, collects results
and evaluates using MLflow GenAI scorers.
"""
import os
import mlflow
from mlflow.genai.scorers.ragas import (
    Faithfulness,
    ContextPrecision,
    ContextRecall
)
from mlflow.genai.scorers.deepeval import AnswerRelevancy
from dotenv import load_dotenv

#------------Import from other packages----------
from logs.logger import get_logger
from evaluation.test_queries import TEST_QUERIES
from app.core.query_router import route_query
from app.core.generator import generate
from app.utils.registry import get_document
from evaluation.mlflow_logger import log_evaluation_run, init_mlflow

load_dotenv()
logger = get_logger()
os.environ["GROQ_API_KEY"] =  os.getenv("GROQ_API_KEY")
evaluator_llm =os.getenv("EVALUATOR_LLM")

def build_eval_data(test_queries: list[dict]) -> list[dict]:
    """
    Runs each test query through RAG pipeline and builds evaluation dataset.
    :param test_queries: list of test query dicts from test_queries.py
    :return: list of dicts with inputs, outputs, context and ground_truth

    Each dict contains:
    - inputs: user question
    - outputs: LLM generated answer
    - context: list of retrieved parent doc texts
    - ground_truth: expected answer from test_queries.py
    """
    try:
        eval_data = []
        for test_query in test_queries:
            query = test_query.get("question","")
            matter = test_query.get("matter","")
            documents = route_query(query, matter)
            response = generate(query, documents)
            ground_truth = test_query.get("ground_truth","")
            eval_dict = {
                "inputs": query,
                "outputs": response,
                "context": [doc["text"] for doc in documents],
                "ground_truth": ground_truth
            }
            eval_data.append(eval_dict)
        return eval_data
    except Exception as e:
        logger.error(f"Got some error while building test data:{e}")
        raise RuntimeError("Got some error while building test data")

def get_eval_params(filename: str, matter: str) -> dict:
    """
    Fetches dynamic chunk config from registry and combines with static params.
    :param filename: PDF filename to fetch chunk config for
    :param matter: client matter
    :return: dict of all eval params for MLflow logging

    Fetches chunk_config from MongoDB registry (dynamic)
    Combines with static params like model names and top_k
    """
    try:
        doc = get_document(filename, matter)
        chunk_config = doc.get("chunk_config", {})
        return {
            "parent_chunk_size": chunk_config.get("parent_chunk", "unknown"),
            "child_chunk_size": chunk_config.get("child_chunk", "unknown"),
            "parent_overlap": chunk_config.get("parent_overlap", "unknown"),
            "child_overlap": chunk_config.get("child_overlap", "unknown"),
            "top_k": 20,
            "embedding_model": "all-MiniLM-L6-v2",
            "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "generator_model": "llama-3.3-70b-versatile",
            "retrieval_strategy": "hybrid_bm25_semantic"
        }
    except Exception as e:
        logger.error(f"Failed to get eval params: {e}")
        raise RuntimeError("Failed to get eval params")


def run_evaluation() -> None:
    """
    Main entry point for evaluation pipeline.
    Builds eval data, runs mlflow.genai.evaluate() and logs params.
    :return: None

    Steps:
    1. build_eval_data(TEST_QUERIES)
    2. mlflow.genai.evaluate(data, scorers=[...])
    3. get_eval_params()
    4. log_evaluation_run(scores, params)
    """
    try:
        init_mlflow()
        logger.info("Building evaluation data...")
        eval_data = build_eval_data(TEST_QUERIES)

        logger.info("Running RAGAs evaluation...")
        results = mlflow.genai.evaluate(
            data=eval_data,
            scorers=[
                Faithfulness(model = f"groq:/{evaluator_llm}"),
                ContextPrecision(model =f"groq:/{evaluator_llm}" ),
                ContextRecall(model =f"groq:/{evaluator_llm}"),
                AnswerRelevancy(model =f"groq:/{evaluator_llm}")
            ]
        )

        logger.info("Logging params to MLflow...")
        params = get_eval_params("microsoft_10k.pdf", "microsoft_2024")
        log_evaluation_run(
            ragas_scores=results.metrics,
            params=params
        )

        logger.info(f"Evaluation complete! Results: {results.metrics}")

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise RuntimeError("Evaluation failed")

if __name__=="__main__":
    run_evaluation()