from fastapi import FastAPI

#-------Imports from other packages---------
from logs.logger import get_logger
from app.routers.ingestion import ingestion_router
from app.routers.documents import document_router

logger = get_logger()
app = FastAPI()

#---------Routers-----------
app.include_router(ingestion_router)
app.include_router(document_router)
