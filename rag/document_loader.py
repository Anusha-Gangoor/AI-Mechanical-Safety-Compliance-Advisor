"""
Document Loader for RAG knowledge base.
Loads .txt and .pdf files from the knowledge base directory,
splits them into chunks, and returns them with source metadata.
"""

import os
import re
from typing import List, Dict, Any


class DocumentChunk:
    """Represents a single chunk of text from a document."""

    def __init__(self, text: str, source: str, chunk_index: int):
        self.text = text
        self.source = source
        self.chunk_index = chunk_index

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "chunk_index": self.chunk_index,
        }

    def __repr__(self) -> str:
        preview = self.text[:60].replace("\n", " ")
        return f"DocumentChunk(source={self.source!r}, chunk={self.chunk_index}, preview={preview!r})"


class DocumentLoader:
    """
    Loads documents from the knowledge base directory and splits them into chunks.
    Supports .txt files by default. PDF support requires PyPDF2.
    """

    def __init__(self, knowledge_base_dir: str, chunk_size: int = 500, chunk_overlap: int = 100):
        self.knowledge_base_dir = knowledge_base_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_all(self) -> List[DocumentChunk]:
        """Load all documents from the knowledge base directory."""
        if not os.path.exists(self.knowledge_base_dir):
            raise FileNotFoundError(
                f"Knowledge base directory not found: {self.knowledge_base_dir}"
            )

        chunks: List[DocumentChunk] = []
        supported_extensions = {".txt", ".pdf"}

        for filename in sorted(os.listdir(self.knowledge_base_dir)):
            filepath = os.path.join(self.knowledge_base_dir, filename)
            ext = os.path.splitext(filename)[1].lower()

            if ext not in supported_extensions:
                continue

            try:
                if ext == ".txt":
                    text = self._read_txt(filepath)
                elif ext == ".pdf":
                    text = self._read_pdf(filepath)
                else:
                    continue

                if text.strip():
                    file_chunks = self._split_text(text, filename)
                    chunks.extend(file_chunks)
            except Exception as e:
                print(f"[DocumentLoader] Warning: Could not load {filename}: {e}")

        return chunks

    def load_file(self, filepath: str) -> List[DocumentChunk]:
        """Load a single file and return its chunks."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".txt":
            text = self._read_txt(filepath)
        elif ext == ".pdf":
            text = self._read_pdf(filepath)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        return self._split_text(text, filename)

    def list_documents(self) -> List[str]:
        """Return list of document filenames in the knowledge base directory."""
        if not os.path.exists(self.knowledge_base_dir):
            return []
        supported = {".txt", ".pdf"}
        return [
            f for f in sorted(os.listdir(self.knowledge_base_dir))
            if os.path.splitext(f)[1].lower() in supported
        ]

    def _read_txt(self, filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def _read_pdf(self, filepath: str) -> str:
        try:
            import PyPDF2
            text_parts = []
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        except ImportError:
            raise ImportError(
                "PyPDF2 is required for PDF support. Install it with: pip install PyPDF2"
            )

    def _split_text(self, text: str, source: str) -> List[DocumentChunk]:
        """
        Split text into overlapping chunks of approximately chunk_size characters.
        Splits on paragraph/section boundaries where possible.
        """
        # Normalize whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Split into paragraphs first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks = []
        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            # If adding this paragraph keeps us under the limit
            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                current_chunk = (current_chunk + "\n\n" + para).strip()
            else:
                # Save current chunk if non-empty
                if current_chunk:
                    chunks.append(
                        DocumentChunk(
                            text=current_chunk,
                            source=source,
                            chunk_index=chunk_index,
                        )
                    )
                    chunk_index += 1

                # If paragraph itself is larger than chunk_size, split by sentence
                if len(para) > self.chunk_size:
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    current_chunk = ""
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                            current_chunk = (current_chunk + " " + sentence).strip()
                        else:
                            if current_chunk:
                                chunks.append(
                                    DocumentChunk(
                                        text=current_chunk,
                                        source=source,
                                        chunk_index=chunk_index,
                                    )
                                )
                                chunk_index += 1
                            current_chunk = sentence
                else:
                    # Add overlap from end of previous chunk
                    if chunks and self.chunk_overlap > 0:
                        overlap_text = chunks[-1].text[-self.chunk_overlap:]
                        current_chunk = overlap_text + "\n\n" + para
                    else:
                        current_chunk = para

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(
                DocumentChunk(
                    text=current_chunk,
                    source=source,
                    chunk_index=chunk_index,
                )
            )

        return chunks
