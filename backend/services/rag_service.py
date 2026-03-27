"""ChromaDB RAG service – document storage and vector search."""

from __future__ import annotations

import chromadb

from backend.config import settings

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks for embedding."""
    if len(text) <= CHUNK_SIZE:
        return [text] if text.strip() else []
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP
    return chunks


class RAGService:
    """Manages ChromaDB collection for RAG documents."""

    def __init__(self):
        self._client: chromadb.ClientAPI | None = None
        self._collection = None

    def _ensure_init(self):
        if self._client is None:
            self._client = chromadb.PersistentClient(path=settings.chromadb_path)
            self._collection = self._client.get_or_create_collection(
                name="evollm_docs",
                metadata={"hnsw:space": "cosine"},
            )

    def add_document(self, doc_id: str, text: str, metadata: dict | None = None):
        """Chunk text and add to ChromaDB."""
        self._ensure_init()
        chunks = _chunk_text(text)
        if not chunks:
            return

        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{**(metadata or {}), "doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]

        self._collection.add(
            ids=ids,
            documents=chunks,
            metadatas=metadatas,
        )

    def query(self, text: str, n_results: int = 5) -> list[str]:
        """Vector search – returns the most relevant text chunks."""
        self._ensure_init()
        try:
            results = self._collection.query(
                query_texts=[text],
                n_results=n_results,
            )
            docs = results.get("documents", [[]])[0]
            return docs
        except Exception:
            return []

    def delete_document(self, doc_id: str):
        """Remove all chunks belonging to a document."""
        self._ensure_init()
        try:
            self._collection.delete(where={"doc_id": doc_id})
        except Exception:
            pass


# Singleton
rag_service = RAGService()
