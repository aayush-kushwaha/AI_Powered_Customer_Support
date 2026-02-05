import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "stub").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

CHROMA_DIR = os.getenv("CHROMA_DIR", "data/vector_db")
DOCS_DIR = os.getenv("DOCS_DIR", "data/documents")
CHAT_LOG = os.getenv("CHAT_LOG", "data/logs/chats.jsonl")
TICKET_LOG = os.getenv("TICKET_LOG", "data/logs/tickets.jsonl")
TOP_K = int(os.getenv("TOP_K", "4"))
