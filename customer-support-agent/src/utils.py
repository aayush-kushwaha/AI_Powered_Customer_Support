import os
import uuid
from datetime import datetime


def now_timestamp() -> str:
    return datetime.utcnow().isoformat() + "Z"


def ensure_dir(path: str) -> None:
    if path:
        os.makedirs(path, exist_ok=True)


def new_session_id() -> str:
    return uuid.uuid4().hex[:12]
