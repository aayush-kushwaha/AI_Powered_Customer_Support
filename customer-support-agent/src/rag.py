import os
from typing import List, Tuple
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from . import config
from .utils import ensure_dir

_vectorstore = None


def load_documents(docs_dir: str) -> List[Tuple[str, str]]:
    docs = []
    if not os.path.isdir(docs_dir):
        return docs
    for name in sorted(os.listdir(docs_dir)):
        path = os.path.join(docs_dir, name)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                docs.append((name, f.read()))
    return docs


def chunk_text(text: str, max_chars: int = 800) -> List[str]:
    chunks = []
    buf = ""
    for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
        if len(buf) + len(para) + 2 <= max_chars:
            buf = (buf + "\n\n" + para).strip()
        else:
            if buf:
                chunks.append(buf)
            if len(para) <= max_chars:
                buf = para
            else:
                # fallback split for very long paragraphs
                for i in range(0, len(para), max_chars):
                    chunks.append(para[i:i + max_chars])
                buf = ""
    if buf:
        chunks.append(buf)
    return chunks


def _get_embeddings():
    return HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)


def build_or_load_vectorstore():
    global _vectorstore
    ensure_dir(config.CHROMA_DIR)
    embeddings = _get_embeddings()
    _vectorstore = Chroma(
        collection_name="support_docs",
        persist_directory=config.CHROMA_DIR,
        embedding_function=embeddings,
    )
    # If empty, ingest
    if _vectorstore._collection.count() == 0:
        docs = load_documents(config.DOCS_DIR)
        texts = []
        metadatas = []
        for doc_name, text in docs:
            for idx, chunk in enumerate(chunk_text(text)):
                texts.append(chunk)
                metadatas.append({"doc": doc_name, "chunk_id": idx})
        if texts:
            _vectorstore.add_texts(texts=texts, metadatas=metadatas)
    return _vectorstore


def retrieve(query: str, top_k: int):
    if _vectorstore is None:
        build_or_load_vectorstore()
    results = _vectorstore.similarity_search_with_score(query, k=top_k)
    chunks = []
    for doc, score in results:
        chunks.append({
            "doc": doc.metadata.get("doc"),
            "chunk_id": doc.metadata.get("chunk_id"),
            "content": doc.page_content,
            "score": float(score),
        })
    return chunks
