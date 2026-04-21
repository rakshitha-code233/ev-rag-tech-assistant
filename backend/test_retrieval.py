#!/usr/bin/env python
"""Test retrieval to debug score issues."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rag_improved import get_embedder, get_index_manager

# Test embedding and search
embedder = get_embedder()
index_manager = get_index_manager()

query = "How do I open the charge port?"
query_embedding = embedder.encode([query], normalize_embeddings=True)
print(f"Query embedding shape: {query_embedding.shape}")

# Load index and search
index_data = index_manager.load_index()
index = index_data["index"]
metadata = index_data["metadata"]["chunks"]

distances, indices = index.search(query_embedding.astype("float32"), 10)
print(f"\nTop 10 results:")
for i, (score, idx) in enumerate(zip(distances[0], indices[0])):
    if idx >= 0 and idx < len(metadata):
        chunk = metadata[idx]
        print(f"  [{i+1}] Score: {score:.4f}, Manual: {chunk.get('manual')}, Page: {chunk.get('page')}")
        print(f"      Text: {chunk.get('text', '')[:60]}...")
