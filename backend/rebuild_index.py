#!/usr/bin/env python
"""Rebuild the RAG index with semantic embeddings."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_improved import build_manual_index

if __name__ == "__main__":
    print("Rebuilding RAG index with semantic embeddings...")
    try:
        result = build_manual_index()
        print(f"✓ Index rebuilt successfully: {result}")
    except Exception as e:
        print(f"✗ Error rebuilding index: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
