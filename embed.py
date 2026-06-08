#!/usr/bin/env python3
"""Embedding and retrieval pipeline using ChromaDB and sentence-transformers."""

import os
from typing import List, Dict, Any

from sentence_transformers import SentenceTransformer
import chromadb

from ingest import load_documents, chunk_documents


CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))
COLLECTION_NAME = "unofficial_guide"
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5


class Embedder:
    def __init__(self):
        print(f"Loading embedding model: {MODEL_NAME} ...")
        self.model = SentenceTransformer(MODEL_NAME)
        print("Connecting to ChromaDB...")
        self.client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        print(f"Using collection: {COLLECTION_NAME}")

    def embed_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 32) -> None:
        """Embed chunks and store them in ChromaDB."""
        # Check if collection already has data
        existing = self.collection.count()
        if existing > 0:
            print(f"Collection already has {existing} items. Clearing before re-ingestion.")
            self.client.delete_collection(name=COLLECTION_NAME)
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )

        texts = [c["text"] for c in chunks]
        ids = [f"{c['source']}:{c['chunk_index']}" for c in chunks]
        metadatas = [{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks]

        print(f"Embedding {len(texts)} chunks in batches of {batch_size}...")
        embeddings = self.model.encode(texts, batch_size=batch_size, show_progress_bar=True)

        print("Storing in ChromaDB...")
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )
        print(f"Stored {len(texts)} chunks.")

    def retrieve(self, query: str, top_k: int = TOP_K) -> List[Dict[str, Any]]:
        """Retrieve top-k chunks for a query, returning list of {text, source, score}."""
        query_embedding = self.model.encode([query])
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        retrieved = []
        for i in range(top_k):
            retrieved.append({
                "text": results["documents"][0][i],
                "source": results["metadatas"][0][i]["source"],
                "chunk_index": results["metadatas"][0][i]["chunk_index"],
                "score": results["distances"][0][i],
            })
        return retrieved


def main() -> None:
    print("Loading and chunking documents...")
    documents = load_documents()
    chunks = chunk_documents(documents)
    print(f"Total chunks: {len(chunks)}")

    embedder = Embedder()
    embedder.embed_chunks(chunks)

    test_queries = [
        "What do students say about DeNero's exam difficulty and grading?",
        "How many hours should students expect to spend on the Gitlet project in CS 61B?",
        "What is the recommended maximum number of hard upper-division CS courses per semester?",
    ]

    print("\n--- Retrieval tests ---\n")
    for q in test_queries:
        print(f"Query: {q}")
        results = embedder.retrieve(q)
        for r in results:
            print(f"  [{r['score']:.3f}] {r['source']} #{r['chunk_index']}")
            preview = r['text'][:200].replace('\n', ' ')
            print(f"      {preview}...")
        print()


if __name__ == "__main__":
    main()
