"""
Session router for managing user session information.
Provides endpoints to fetch, delete session ids and their associated queries and also provice past history
for the authenticated user.
"""

from typing import Annotated
from fastapi import APIRouter, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

#----------Import from other packages----------
from app.common.structured_models import SessionResponse, DeleteSessionID
from app.core.security import get_current_user
from app.utils.mongo import get_checkpointer_collection, get_user_session_mapping
from app.core.session_management import extract_conversation_from_checkpoints
from logs.logger import get_logger

logger = get_logger()
limiter = Limiter(key_func=get_remote_address)
session_router = APIRouter()


@session_router.get("/session_ids", tags=["Session"])
@limiter.limit("30/minute")
def get_session_ids(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)]
) -> list[SessionResponse]:
    """
    Retrieves all session ids and their queries for the authenticated user.
    :param request:
    :param current_user:
    :return: list of SessionResponse
    """
    try:
        email = current_user.get("email")
        if not email:
            logger.error("No email found in current_user")
            raise ValueError("User email not found")

        collection = get_user_session_mapping()

        doc = collection.find_one(
            {"email": email},
            {"_id": 0, "sessions": 1}
        )

        if not doc or "sessions" not in doc:
            return []

        sessions = doc.get("sessions", [])

        return [
            SessionResponse(
                session_id=s["session_id"],
                query=s["query"]
            )
            for s in sessions
        ]

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        raise RuntimeError("Error fetching sessions")


@session_router.delete("/delete_session", tags=["Session"])
@limiter.limit("30/minute")
def delete_session(
    request: Request,
    input: DeleteSessionID,
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    """
    Deletes a specific session for the authenticated user.
    :param request:
    :param input:
    :param current_user:
    :return: status message
    """
    try:
        email = current_user.get("email")
        if not email:
            logger.error("No email found in current_user")
            raise ValueError("User email not found")

        session_id = input.session_id
        if not session_id:
            logger.error("No session_id provided")
            raise ValueError("Session ID is required")

        collection = get_user_session_mapping()

        result = collection.update_one(
            {"email": email},
            {
                "$pull": {
                    "sessions": {"session_id": session_id}
                }
            }
        )

        if result.modified_count == 0:
            return {
                "status": "success",
                "message": "Session not found or already deleted"
            }

        return {
            "status": "success",
            "message": "Session deleted successfully"
        }

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise RuntimeError("Error deleting session")


@session_router.get("/conversation/{session_id}", tags=["Session"])
@limiter.limit("30/minute")
def get_conversation(
    request: Request,
    session_id: str,
    current_user: Annotated[dict, Depends(get_current_user)]
) -> list[dict]:
    """
    Retrieves conversation history for a given session_id.
    :param request:
    :param session_id:
    :param current_user:
    :return: list of conversation messages
    """
    try:
        email = current_user.get("email")
        if not email:
            raise ValueError("User email not found")

        session_collection = get_user_session_mapping()
        exists = session_collection.find_one(
            {"email": email, "sessions.session_id": session_id}
        )
        if not exists:
            raise ValueError("Session not found for this user")

        checkpointer_collection = get_checkpointer_collection()
        docs = list(
            checkpointer_collection
            .find({"thread_id": session_id})
            .sort("_id", 1)
        )

        if not docs:
            return []

        return extract_conversation_from_checkpoints(docs)

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation: {e}")
        raise RuntimeError("Error fetching conversation")