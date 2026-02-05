import uuid
from .utils import now_timestamp
from .logger import log_ticket


def create_ticket(session_id: str, user_message: str) -> str:
    ticket_id = uuid.uuid4().hex[:8]
    entry = {
        "timestamp": now_timestamp(),
        "ticket_id": ticket_id,
        "session_id": session_id,
        "message": user_message,
    }
    log_ticket(entry)
    return ticket_id
