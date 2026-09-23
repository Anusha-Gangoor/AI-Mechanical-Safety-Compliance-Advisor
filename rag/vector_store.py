"""
Vector Store for RAG system.
Uses FAISS for local vector similarity search with TF-IDF style embeddings
(via scikit-learn TfidfVectorizer) as a lightweight, dependency-friendly option.
Falls back to simple keyword matching if scikit-learn is unavailable.
"""

import os
import json
import pickle
import numpy as np
from typing import List, Tuple, Optional, Dict, Any

from .document_loader import DocumentChunk


class VectorStore:
    """
    Stores document chunks with vector embeddings and provides similarity search.

    Uses TF-IDF vectorization (scikit-learn) for embeddings. This avoids the need
    for heavy models while still providing meaningful similarity matching.

    If scikit-learn is unavailable, falls back to keyword-based matching.
    """

    INDEX_FILE = "vector_index.pkl"
    CHUNKS_FILE = "chunks.json"

    def __init__(self, index_dir: str):
        self.index_dir = index_dir
        self.chunks: List[DocumentChunk] = []
        self.vectors: Optional[np.ndarray] = None
        self.vectorizer = None
        self._use_tfidf = False

        os.makedirs(index_dir, exist_ok=True)
        self._init_vectorizer()

    def _init_vectorizer(self):
        """Initialize the TF-IDF vectorizer."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words="english",
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            self._use_tfidf = True
        except ImportError:
            self._use_tfidf = False

    def build(self, chunks: List[DocumentChunk]) -> None:
        """Build the vector index from a list of document chunks."""
        if not chunks:
            raise ValueError("Cannot build index from empty chunk list.")

        self.chunks = chunks
        texts = [c.text for c in chunks]

        if self._use_tfidf:
            self.vectors = self.vectorizer.fit_transform(texts).toarray()
        else:
            # Fallback: store just the texts (keyword search)
            self.vectors = None

    def save(self) -> None:
        """Persist the vector index and chunks to disk."""
        # Save chunks as JSON
        chunks_path = os.path.join(self.index_dir, self.CHUNKS_FILE)
        chunks_data = [c.to_dict() for c in self.chunks]
        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2)

        # Save vectorizer and matrix
        if self._use_tfidf and self.vectorizer is not None:
            index_path = os.path.join(self.index_dir, self.INDEX_FILE)
            with open(index_path, "wb") as f:
                pickle.dump({"vectorizer": self.vectorizer, "vectors": self.vectors}, f)

    def load(self) -> bool:
        """
        Load a previously saved index from disk.
        Returns True if successful, False if index not found.
        """
        chunks_path = os.path.join(self.index_dir, self.CHUNKS_FILE)
        index_path = os.path.join(self.index_dir, self.INDEX_FILE)

        if not os.path.exists(chunks_path):
            return False

        # Load chunks
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)

        self.chunks = [
            DocumentChunk(
                text=c["text"],
                source=c["source"],
                chunk_index=c["chunk_index"],
            )
            for c in chunks_data
        ]

        # Load TF-IDF index if available
        if self._use_tfidf and os.path.exists(index_path):
            with open(index_path, "rb") as f:
                data = pickle.load(f)
            self.vectorizer = data["vectorizer"]
            self.vectors = data["vectors"]

        return True

    def is_built(self) -> bool:
        """Return True if the index is built and ready for search."""
        chunks_path = os.path.join(self.index_dir, self.CHUNKS_FILE)
        return os.path.exists(chunks_path) and len(self.chunks) > 0

    def search(self, query: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """
        Search for the most relevant document chunks for a given query.
        Returns a list of (DocumentChunk, score) tuples sorted by relevance (descending).
        """
        if not self.chunks:
            return []

        if self._use_tfidf and self.vectorizer is not None and self.vectors is not None:
            return self._tfidf_search(query, top_k)
        else:
            return self._keyword_search(query, top_k)

    def _tfidf_search(
        self, query: str, top_k: int
    ) -> List[Tuple[DocumentChunk, float]]:
        """TF-IDF cosine similarity search."""
        from sklearn.metrics.pairwise import cosine_similarity

        query_vec = self.vectorizer.transform([query]).toarray()
        scores = cosine_similarity(query_vec, self.vectors)[0]

        # Get top-k indices sorted by score
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score > 0.0:
                results.append((self.chunks[idx], score))

        return results

    def _keyword_search(
        self, query: str, top_k: int
    ) -> List[Tuple[DocumentChunk, float]]:
        """Simple keyword matching fallback."""
        query_words = set(query.lower().split())
        results = []

        for chunk in self.chunks:
            chunk_words = set(chunk.text.lower().split())
            overlap = len(query_words & chunk_words)
            if overlap > 0:
                score = overlap / max(len(query_words), 1)
                results.append((chunk, float(score)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about the vector store."""
        sources = {}
        for chunk in self.chunks:
            sources[chunk.source] = sources.get(chunk.source, 0) + 1

        return {
            "total_chunks": len(self.chunks),
            "total_documents": len(sources),
            "documents": sources,
            "vectorizer_type": "TF-IDF (sklearn)" if self._use_tfidf else "Keyword (fallback)",
        }
