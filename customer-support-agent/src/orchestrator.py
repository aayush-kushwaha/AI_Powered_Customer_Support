import re
from typing import Optional
from . import config
from .utils import now_timestamp
from .logger import log_chat
from .memory import get_history, append_turn, trim_history
from .rag import retrieve
from .prompts import format_prompt
from .actions import create_ticket


def _ticket_intent(message: str) -> bool:
    keywords = [
        "refund", "complaint", "not working", "issue", "bug",
        "cancel", "support ticket", "ticket",
    ]
    msg = message.lower()
    return any(k in msg for k in keywords)


def _user_confirmed(message: str) -> bool:
    return bool(re.search(r"\byes\b", message.lower()))


def _call_llm(prompt: str, context_chunks):
    provider = config.LLM_PROVIDER
    if provider == "groq" and config.GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=config.GROQ_API_KEY)
            resp = client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[{"role": "system", "content": prompt}],
                temperature=0.2,
            )
            return resp.choices[0].message.content
        except Exception:
            pass

    if provider == "openai" and config.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "system", "content": prompt}],
                temperature=0.2,
            )
            return resp.choices[0].message.content
        except Exception:
            pass

    # Stub fallback
    if context_chunks:
        sources = ", ".join(sorted({c["doc"] for c in context_chunks if c.get("doc")}))
        return (
            f"(Stub) I found relevant info in: {sources}. "
            f"Based on that context, here's a brief answer: {context_chunks[0]['content'][:200]}"
        )
    return "(Stub) I don't have enough context. Would you like me to create a support ticket?"


def handle_message(session_id: str, message: str) -> dict:
    history = get_history(session_id)
    context_chunks = retrieve(message, config.TOP_K)
    has_context = len(context_chunks) > 0
    ticket_intent = _ticket_intent(message)

    route = "rag"
    ticket_id: Optional[str] = None

    if not has_context:
        route = "escalate"
        response = "I don't have enough context to answer that. Would you like me to create a support ticket?"
        if ticket_intent and _user_confirmed(message):
            ticket_id = create_ticket(session_id, message)
            route = "ticket"
            response = f"Ticket created. Your ticket id is {ticket_id}."
    else:
        prompt = format_prompt(history, context_chunks, message)
        response = _call_llm(prompt, context_chunks)
        if ticket_intent and _user_confirmed(message):
            ticket_id = create_ticket(session_id, message)
            route = "ticket"
            response = f"Ticket created. Your ticket id is {ticket_id}."

    append_turn(session_id, "user", message)
    append_turn(session_id, "assistant", response)
    trim_history(session_id, max_turns=6)

    log_chat({
        "timestamp": now_timestamp(),
        "session_id": session_id,
        "route": route,
        "user_message": message,
        "response": response,
        "sources": [
            {"doc": c.get("doc"), "chunk_id": c.get("chunk_id"), "score": c.get("score")}
            for c in context_chunks
        ],
    })

    return {
        "session_id": session_id,
        "response": response,
        "route": route,
        "sources": [
            {"doc": c.get("doc"), "chunk_id": c.get("chunk_id")}
            for c in context_chunks
        ],
        "ticket_id": ticket_id,
    }
