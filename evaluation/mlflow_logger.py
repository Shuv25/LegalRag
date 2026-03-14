"""
MLflow logging utility for Legal RAG evaluation.
Integrates with DagsHub for experiment tracking, metric logging,
prompt versioning and retrieval statistics for the RAG pipeline.
"""

import os
import dagshub
import mlflow
from dotenv import load_dotenv

#-----------Import from other packages------------
from logs.logger import get_logger
from app.core.prompts import GENERATOR_PROMPT,ROUTER_PROMPT,GENERAL_PROMPT

load_dotenv()
logger = get_logger()

def init_mlflow() -> None:
    """
    Initializes MLflow tracking with DagsHub integration.
    Sets up experiment for legal RAG evaluation.
    Should be called once during app lifespan startup.
    :return: None
    """
    try:
        dagshub.init(
            repo_owner=os.getenv('DAGSHUB_USERNAME'),
            repo_name=os.getenv('DAGSHUB_REPONAME'),
            mlflow=True)
        mlflow.set_experiment("legal-rag-evaluation")
        mlflow.set_tracking_uri(os.getenv('DAGSHUB_TRACKING_URI'))
        mlflow.langchain.autolog()
        logger.info("mlflow initialized")
    except Exception as e:
        logger.error(f"Got some error while initializing mlflow:{e}")
        raise RuntimeError("Mlflow initialization failed")

def log_evaluation_run(ragas_scores: dict, params: dict) -> None:
    """
    Logs a complete RAGAs evaluation run to MLflow.
    Records pipeline parameters, RAGAs metrics and prompt artifacts.
    :param ragas_scores: dict of RAGAs metric names and scores
    :param params: dict of pipeline configuration parameters
    :return: None
    """
    try:
        with mlflow.start_run():
            mlflow.log_params(params)
            mlflow.log_metrics(ragas_scores)
    except Exception as e:
        logger.error(f"Failed to log params and metrices: {e}")
        raise RuntimeError("Failed to log params and metrices")


def register_prompts() -> None:
    try:
        client = mlflow.MlflowClient()

        prompts = {
            "generator_prompt": GENERATOR_PROMPT,
            "router_prompt": ROUTER_PROMPT,
            "general_prompt": GENERAL_PROMPT
        }

        for name, template in prompts.items():
            try:
                client.get_prompt(name)
                logger.info(f"Prompt '{name}' already registered, skipping!")
            except Exception:
                mlflow.genai.register_prompt(
                    name=name,
                    template=template,
                )
                logger.info(f"Prompt '{name}' registered!")

    except Exception as e:
        logger.error(f"Failed to register prompts: {e}")
        raise RuntimeError("Failed to register prompts")


def load_prompt_from_registry(name: str, version: int) -> str:
    """
    Loads a specific prompt version from MLflow Prompt Registry.
    :param name: registered prompt name
    :param version: version number to load
    :return: prompt template string
    """
    try:
        prompt = mlflow.genai.load_prompt(f"prompts:/{name}/{version}")
        logger.info(f"Loaded prompt '{name}' version {version}")
        return prompt.template
    except Exception as e:
        logger.error(f"Failed to load prompt '{name}': {e}")
        raise RuntimeError(f"Failed to load prompt '{name}'")
