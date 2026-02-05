# AI-Powered Customer Support Platform

A simple, internship-ready customer support agent that answers questions using RAG over local documents, keeps short session memory, and can create support tickets.

## How to run

1. Create a virtual environment and install deps.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set env vars (optional) and run.

```bash
cp .env.example .env
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

## Streamlit UI (optional)

Run the API first, then start the UI in a second terminal:

```bash
streamlit run streamlit_app.py
```

If your API is not at `http://localhost:8000`, set:

```bash
export API_URL=http://localhost:8000
```

## Example usage

```bash
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"How do I get a refund?"}'
```

## Documents

Put support documents in `data/documents/`. On startup, the app loads all files, chunks by paragraph, and indexes them into ChromaDB at `data/vector_db/`.

## Escalation and tickets

If the agent cannot find relevant context, it will ask to create a ticket. If the user confirms, a ticket is written to `data/logs/tickets.jsonl`.

Chat logs are appended to `data/logs/chats.jsonl`.
