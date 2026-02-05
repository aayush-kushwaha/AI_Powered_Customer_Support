SYSTEM_PROMPT = (
    "You are a helpful customer support assistant. "
    "Answer only using the provided context. "
    "If the context is insufficient, say you don't know and ask if the user wants to create a support ticket."
)


def format_prompt(history, context_chunks, user_message: str) -> str:
    context_text = "\n\n".join(
        [f"[{c['doc']} #{c['chunk_id']}] {c['content']}" for c in context_chunks]
    )
    history_text = "\n".join([f"{h['role']}: {h['text']}" for h in history])

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Context:\n{context_text or 'None'}\n\n"
        f"Conversation:\n{history_text or 'None'}\n\n"
        f"User: {user_message}\n"
        f"Assistant:"
    )
