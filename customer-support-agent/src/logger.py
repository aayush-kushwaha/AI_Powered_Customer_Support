import json
import os
from .utils import ensure_dir
from . import config


def _append_jsonl(path: str, entry: dict) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_chat(entry: dict) -> None:
    _append_jsonl(config.CHAT_LOG, entry)


def log_ticket(entry: dict) -> None:
    _append_jsonl(config.TICKET_LOG, entry)
