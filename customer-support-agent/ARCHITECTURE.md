# Architecture

```
Client -> FastAPI /chat
        -> Orchestrator
            -> Memory
            -> RAG Retriever (ChromaDB)
            -> LLM (Groq/OpenAI/Stub)
            -> Logs + Tickets
```

## Request flow

1. API receives a message and session_id.
2. Orchestrator loads history, retrieves top_k chunks.
3. If context is missing, it escalates and asks about a ticket.
4. Otherwise it builds a prompt and calls the LLM (or stub).
5. Logs chat and optionally creates a ticket.

## Tradeoffs and limitations

- Simple paragraph chunking may miss context across long sections.
- In-memory session history is not persisted across restarts.
- Stub LLM is intentionally basic for offline testing.
