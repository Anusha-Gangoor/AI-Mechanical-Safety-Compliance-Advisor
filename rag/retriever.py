"""
Retriever module: orchestrates document loading, indexing, and retrieval.
This is the main entry point for the RAG pipeline.
"""

import os
from typing import List, Dict, Any, Optional

from .document_loader import DocumentLoader, DocumentChunk
from .vector_store import VectorStore


class RetrievedContext:
    """Encapsulates retrieved RAG results with metadata."""

    def __init__(
        self,
        query: str,
        chunks: List[DocumentChunk],
        scores: List[float],
    ):
        self.query = query
        self.chunks = chunks
        self.scores = scores

    @property
    def context_text(self) -> str:
        """Return the combined text of all retrieved chunks."""
        if not self.chunks:
            return ""
        parts = []
        for i, chunk in enumerate(self.chunks):
            parts.append(
                f"[Context {i+1} | Source: {chunk.source}]\n{chunk.text}"
            )
        return "\n\n---\n\n".join(parts)

    @property
    def sources(self) -> List[str]:
        """Return deduplicated list of source document names."""
        seen = set()
        result = []
        for chunk in self.chunks:
            if chunk.source not in seen:
                seen.add(chunk.source)
                result.append(chunk.source)
        return result

    @property
    def is_empty(self) -> bool:
        return len(self.chunks) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "sources": self.sources,
            "chunks": [c.to_dict() for c in self.chunks],
            "scores": self.scores,
            "context_text": self.context_text,
        }


class Retriever:
    """
    Orchestrates the RAG pipeline:
    1. Load documents from knowledge base
    2. Build / load vector index
    3. Retrieve relevant chunks for a query
    """

    def __init__(
        self,
        knowledge_base_dir: str,
        index_dir: str,
        top_k: int = 5,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ):
        self.knowledge_base_dir = knowledge_base_dir
        self.index_dir = index_dir
        self.top_k = top_k

        self.loader = DocumentLoader(
            knowledge_base_dir=knowledge_base_dir,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self.store = VectorStore(index_dir=index_dir)
        self._initialized = False

    def initialize(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Initialize the retriever. Loads existing index or builds a new one.
        Returns a status dict with stats.
        """
        # Try loading existing index first (unless forced rebuild)
        if not force_rebuild and self.store.load():
            self._initialized = True
            stats = self.store.get_stats()
            stats["status"] = "loaded_from_cache"
            return stats

        # Build fresh index
        try:
            chunks = self.loader.load_all()
            if not chunks:
                return {
                    "status": "error",
                    "error": "No documents found in knowledge base.",
                    "total_chunks": 0,
                }

            self.store.build(chunks)
            self.store.save()
            self._initialized = True

            stats = self.store.get_stats()
            stats["status"] = "built_fresh"
            return stats

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "total_chunks": 0,
            }

    def retrieve(self, query: str, top_k: Optional[int] = None) -> RetrievedContext:
        """
        Retrieve the most relevant document chunks for a query.

        Args:
            query: The search query (typically machine data + context).
            top_k: Number of chunks to retrieve (defaults to self.top_k).

        Returns:
            RetrievedContext object with chunks, scores, and metadata.
        """
        if not self._initialized:
            self.initialize()

        k = top_k if top_k is not None else self.top_k
        results = self.store.search(query, top_k=k)

        chunks = [r[0] for r in results]
        scores = [r[1] for r in results]

        return RetrievedContext(query=query, chunks=chunks, scores=scores)

    def add_document(self, filepath: str) -> Dict[str, Any]:
        """
        Add a new document to the knowledge base and rebuild the index.
        Returns status dict.
        """
        try:
            new_chunks = self.loader.load_file(filepath)
            existing_chunks = list(self.store.chunks)
            all_chunks = existing_chunks + new_chunks

            self.store.build(all_chunks)
            self.store.save()
            self._initialized = True

            stats = self.store.get_stats()
            stats["status"] = "document_added"
            stats["new_chunks"] = len(new_chunks)
            return stats
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """Return current index statistics."""
        if not self._initialized:
            return {"status": "not_initialized", "total_chunks": 0}
        return self.store.get_stats()

    def list_documents(self) -> List[str]:
        """List all documents in the knowledge base directory."""
        return self.loader.list_documents()

    def is_ready(self) -> bool:
        return self._initialized and len(self.store.chunks) > 0
