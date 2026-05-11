#!/usr/bin/env python
"""Start Flask development server with proper initialization."""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Initialize database and rebuild index
print("Initializing system...")
from db import init_db
from rag_improved import build_manual_index

init_db()
print("✓ Database initialized")

# Rebuild index for user 1
result = build_manual_index(user_id=1)
print(f"✓ Index rebuilt: {result['manuals_indexed']} manuals, {result['chunks_indexed']} chunks")

# Start Flask app
print("\nStarting Flask server on http://localhost:5000")
from flask_api import app
app.run(host="0.0.0.0", port=5000, debug=True)
