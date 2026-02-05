import json
import os
import uuid
from .utils import now_timestamp
from .logger import log_ticket
from . import config


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


def find_ticket(ticket_id: str) -> dict | None:
    path = config.TICKET_LOG
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("ticket_id") == ticket_id:
                    return entry
    except OSError:
        return None
    return None
