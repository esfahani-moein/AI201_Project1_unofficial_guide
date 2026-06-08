#!/usr/bin/env python3
"""Document ingestion and chunking pipeline for The Unofficial Guide."""

from pathlib import Path
from typing import List, Dict, Any


DOCUMENTS_DIR = Path(__file__).parent / "documents"
CHUNK_SIZE = 400
OVERLAP = 100


def load_documents(doc_dir: Path = DOCUMENTS_DIR) -> List[Dict[str, Any]]:
    """Load all .txt files from doc_dir, returning list of {source, text} dicts."""
    docs = []
    for txt_file in sorted(doc_dir.glob("*.txt")):
        text = txt_file.read_text(encoding="utf-8")
        # Basic cleaning: strip excessive whitespace and blank lines
        lines = [line.strip() for line in text.splitlines()]
        cleaned = "\n".join(line for line in lines if line)
        docs.append({"source": txt_file.name, "text": cleaned})
    return docs


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> List[str]:
    """Split text into overlapping chunks of at most chunk_size characters."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        # Trim to last newline or space to avoid cutting words if possible
        if end < len(text):
            # Try to break at a newline first
            last_newline = chunk.rfind("\n")
            if last_newline > chunk_size // 2:
                end = start + last_newline
                chunk = text[start:end]
            else:
                # Fallback to last space
                last_space = chunk.rfind(" ")
                if last_space > chunk_size // 2:
                    end = start + last_space
                    chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end - overlap
        if start >= end:
            # Safety: overlap too large or chunk empty
            start = end
    # Filter out empty chunks
    return [c for c in chunks if c]


def chunk_documents(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Split loaded documents into chunks, preserving source metadata."""
    all_chunks = []
    for doc in docs:
        text = doc["text"]
        raw_chunks = chunk_text(text)
        for idx, chunk in enumerate(raw_chunks):
            all_chunks.append({
                "source": doc["source"],
                "chunk_index": idx,
                "text": chunk,
            })
    return all_chunks


def inspect_chunks(chunks: List[Dict[str, Any]], n: int = 5) -> None:
    """Print N representative chunks for manual inspection."""
    print(f"--- Inspecting {n} random chunks ---\n")
    import random
    sample = random.sample(chunks, min(n, len(chunks)))
    for c in sample:
        print(f"Source: {c['source']} (chunk #{c['chunk_index']})")
        print(f"Length: {len(c['text'])} chars")
        print(f"Text:\n{c['text'][:500]}{'...' if len(c['text']) > 500 else ''}")
        print("-" * 60)


if __name__ == "__main__":
    print("Loading documents...")
    documents = load_documents()
    print(f"Loaded {len(documents)} documents.")

    print("Chunking...")
    chunks = chunk_documents(documents)
    print(f"Total chunks: {len(chunks)}")

    inspect_chunks(chunks, n=5)
