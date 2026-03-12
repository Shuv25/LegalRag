from app.routers.documents import document_router
from app.routers.ingestion import ingestion_router
from app.routers.retrieval import retrieval_router

__all__=['document_router',
         'ingestion_router',
         'retrieval_router']