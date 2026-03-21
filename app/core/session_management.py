"""
Session management utilities for extracting conversation history
from MongoDB checkpointer.
"""

import msgpack
from typing import List, Dict
from pymongo.collection import Collection

#----------Import from other packages----------
from logs.logger import get_logger

logger = get_logger()

def upsert_user_session(
    collection: Collection,
    email: str,
    session_id: str,
    query: str,
    max_sessions: int = 10
):
    """
    Inserts or updates user session mapping.
    Ensures unique email and session_id, stores first query,
    and limits number of sessions per user.
    :param collection: MongoDB session_mapping collection
    :param email: user email
    :param session_id: unique session id
    :param query: user query
    :param max_sessions: max allowed sessions per user
    :return: None
    """

    words = query.split()
    query_label = query if len(words) <= 3 else " ".join(words[:4])

    doc = collection.find_one({"email": email}, {"sessions": 1})
    if doc:
        sessions = doc.get("sessions", [])
        if len(sessions) >= max_sessions and all(s["session_id"] != session_id for s in sessions):
            raise ValueError("Session limit exceeded (max 10 sessions allowed)")

    collection.update_one(
        {
            "email": email,
            "sessions.session_id": {"$ne": session_id}
        },
        {
            "$setOnInsert": {"email": email},
            "$push": {
                "sessions": {
                    "session_id": session_id,
                    "query": query_label
                }
            }
        },
        upsert=True
    )

def extract_conversation_from_checkpoints(docs: list) -> List[Dict]:
    """
    Decodes checkpoint documents and extracts conversation messages.
    Formats messages into 'user' and 'AI' roles after decoding.

    :param docs: list of checkpoint documents
    :return: list of conversation messages
    """
    conversations: List[Dict] = []

    for doc in docs:
        binary_data = doc.get("checkpoint")
        if not binary_data:
            continue

        try:
            decoded = msgpack.unpackb(binary_data, raw=False)
        except Exception:
            continue

        messages = decoded.get("channel_values", {}).get("messages", [])

        for msg in messages:
            content = msg.get("content")
            if not content:
                continue

            role = msg.get("role")

            if role == "user":
                final_role = "user"
            else:
                final_role = "AI"

            conversations.append({
                "role": final_role,
                "content": content
            })

    return conversations

