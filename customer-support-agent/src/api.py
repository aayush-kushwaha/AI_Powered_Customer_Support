from fastapi import FastAPI
from pydantic import BaseModel
from .rag import build_or_load_vectorstore
from .utils import new_session_id
from .orchestrator import handle_message
from . import config
import os

app = FastAPI(title="AI-Powered Customer Support Platform")


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


@app.on_event("startup")
def _startup():
    build_or_load_vectorstore()


@app.get("/health")
def health():
    vector_exists = os.path.isdir(config.CHROMA_DIR)
    return {"status": "ok", "vector_store": vector_exists}


@app.post("/chat")
def chat(req: ChatRequest):
    session_id = req.session_id or new_session_id()
    result = handle_message(session_id, req.message)
    return result
