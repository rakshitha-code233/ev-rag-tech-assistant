#!/usr/bin/env python
"""Rebuild the RAG index for user 1's manual."""

from rag_improved import build_manual_index

result = build_manual_index(user_id=1)
print(f"✓ Index built successfully!")
print(f"  Manuals indexed: {result['manuals_indexed']}")
print(f"  Chunks indexed: {result['chunks_indexed']}")
