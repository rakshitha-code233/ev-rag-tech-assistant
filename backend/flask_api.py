"""
Flask REST API for EV Diagnostic Assistant.
Wraps existing rag.py, db.py, and manual_query.py logic.
The Streamlit app (rag_app.py) is left untouched.
"""

import json
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

import jwt
from flask import Flask, jsonify, request
from flask_cors import CORS

from db import init_db, login_user, register_user
from manual_query import get_answer
from rag import DATA_DIR, build_manual_index, list_manual_files

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

FRONTEND_URL = os.getenv("FRONTEND_URL", "")

_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://ev-rag-tech-assistant-frontend.onrender.com",
]
if FRONTEND_URL and FRONTEND_URL not in _cors_origins:
    _cors_origins.append(FRONTEND_URL)

app = Flask(__name__)
CORS(
    app,
    origins=_cors_origins,
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Type"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    supports_credentials=False,
)

BASE_DIR = Path(__file__).resolve().parent
USERS_DB = BASE_DIR / "users.db"

JWT_SECRET = os.getenv("JWT_SECRET", "ev_diag_secret_change_in_production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def get_db():
    conn = sqlite3.connect(str(USERS_DB))
    conn.row_factory = sqlite3.Row
    return conn


def init_chat_history_table():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id),
            title      TEXT NOT NULL,
            messages   TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def create_token(user: dict) -> str:
    payload = {
        "sub": str(user["id"]),  # must be string for PyJWT >= 2.x
        "username": user["username"],
        "email": user["email"],
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            app.logger.debug("require_auth: missing/invalid Authorization header: %r", auth_header[:60])
            return jsonify({"error": "Missing or invalid token"}), 401
        token = auth_header[len("Bearer "):]
        payload = decode_token(token)
        if payload is None:
            app.logger.debug("require_auth: token decode failed, token prefix: %r", token[:20])
            return jsonify({"error": "Token expired or invalid"}), 401
        request.current_user = payload
        request.current_user['sub'] = int(payload['sub'])  # convert back to int
        return f(*args, **kwargs)

    return decorated


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not username or not email or not password:
        return jsonify({"error": "username, email, and password are required"}), 400

    result = register_user(username, email, password)
    if result == "exists":
        return jsonify({"error": "An account with this email already exists"}), 409
    return jsonify({"message": "Account created successfully"}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = login_user(email, password)
    if user is None:
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_token(user)
    return jsonify(
        {
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
            },
        }
    )


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------


@app.route("/api/chat", methods=["POST"])
@require_auth
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        answer = get_answer(message)
    except Exception as exc:
        return jsonify({"error": f"Chat service error: {exc}"}), 500

    return jsonify({"answer": answer})


# ---------------------------------------------------------------------------
# Transcription endpoint
# ---------------------------------------------------------------------------


@app.route("/api/chat/transcribe", methods=["POST"])
@require_auth
def transcribe():
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        return jsonify({"error": "Transcription service unavailable"}), 503

    app.logger.info("transcribe: content_type=%r files=%r form=%r", 
                    request.content_type, list(request.files.keys()), list(request.form.keys()))

    if "audio" not in request.files:
        return jsonify({"error": f"audio file is required. Got files: {list(request.files.keys())}, content_type: {request.content_type}"}), 400

    audio_file = request.files["audio"]
    suffix = Path(audio_file.filename or "recording.webm").suffix or ".webm"

    try:
        from groq import Groq

        client = Groq(api_key=groq_key)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            audio_file.save(tmp.name)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as handle:
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=handle,
                language="en",
                response_format="text",
                temperature=0.0,
            )
        Path(tmp_path).unlink(missing_ok=True)
        text = transcript.strip() if isinstance(transcript, str) else str(transcript).strip()
        return jsonify({"transcript": text})
    except Exception as exc:
        return jsonify({"error": f"Transcription failed: {exc}"}), 503


# ---------------------------------------------------------------------------
# Manuals endpoints
# ---------------------------------------------------------------------------


def _manual_meta(path: Path) -> dict:
    stat = path.stat()
    return {
        "filename": path.name,
        "size": stat.st_size,
        "uploaded_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


@app.route("/api/manuals", methods=["GET"])
@require_auth
def list_manuals():
    manuals = [_manual_meta(p) for p in list_manual_files()]
    return jsonify(manuals)


@app.route("/api/manuals/upload", methods=["POST"])
@require_auth
def upload_manual():
    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400

    uploaded = request.files["file"]
    if not uploaded.filename or not uploaded.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dest = DATA_DIR / uploaded.filename

    if dest.exists():
        return jsonify({"error": "A manual with this name already exists"}), 409

    uploaded.save(str(dest))

    try:
        build_manual_index()
    except Exception:
        pass  # Index rebuild is best-effort; file is saved regardless

    return jsonify(_manual_meta(dest)), 201


@app.route("/api/manuals/<path:filename>", methods=["DELETE"])
@require_auth
def delete_manual(filename: str):
    target = DATA_DIR / filename
    if not target.exists():
        return jsonify({"error": "Manual not found"}), 404

    target.unlink()

    try:
        build_manual_index()
    except Exception:
        pass

    return jsonify({"message": f"{filename} deleted successfully"})


# ---------------------------------------------------------------------------
# History endpoints
# ---------------------------------------------------------------------------


@app.route("/api/history", methods=["GET"])
@require_auth
def get_history():
    user_id = request.current_user["sub"]
    conn = get_db()
    rows = conn.execute(
        "SELECT id, title, messages, created_at FROM chat_history WHERE user_id=? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()

    result = []
    for row in rows:
        try:
            messages = json.loads(row["messages"])
        except Exception:
            messages = []
        result.append(
            {
                "id": row["id"],
                "title": row["title"],
                "messages": messages,
                "created_at": row["created_at"],
            }
        )
    return jsonify(result)


@app.route("/api/history/<int:conversation_id>", methods=["GET"])
@require_auth
def get_conversation(conversation_id: int):
    user_id = request.current_user["sub"]
    conn = get_db()
    row = conn.execute(
        "SELECT id, title, messages, created_at FROM chat_history WHERE id=? AND user_id=?",
        (conversation_id, user_id),
    ).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "Conversation not found"}), 404
    try:
        messages = json.loads(row["messages"])
    except Exception:
        messages = []
    return jsonify({
        "id": row["id"],
        "title": row["title"],
        "messages": messages,
        "created_at": row["created_at"],
    })


@app.route("/api/history/<int:conversation_id>", methods=["PUT"])
@require_auth
def update_conversation(conversation_id: int):
    user_id = request.current_user["sub"]
    data = request.get_json(silent=True) or {}
    messages = data.get("messages") or []

    conn = get_db()
    result = conn.execute(
        "UPDATE chat_history SET messages=? WHERE id=? AND user_id=?",
        (json.dumps(messages), conversation_id, user_id),
    )
    conn.commit()
    conn.close()

    if result.rowcount == 0:
        return jsonify({"error": "Conversation not found"}), 404
    return jsonify({"id": conversation_id})


@app.route("/api/history", methods=["POST"])
@require_auth
def save_history():
    user_id = request.current_user["sub"]
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    messages = data.get("messages") or []

    if not title:
        return jsonify({"error": "title is required"}), 400

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO chat_history (user_id, title, messages) VALUES (?, ?, ?)",
        (user_id, title[:80], json.dumps(messages)),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": new_id}), 201


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


@app.route("/api/health", methods=["GET"])
def health():
    transcription_available = bool(os.getenv("GROQ_API_KEY"))
    return jsonify({"status": "ok", "transcription_available": transcription_available})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

# Initialize DB tables on startup — runs for both gunicorn and direct execution
init_db()
init_chat_history_table()

# Always rebuild RAG index on startup to ensure compatibility with current faiss/numpy versions
try:
    from rag import list_manual_files, build_manual_index
    manuals = list_manual_files()
    if manuals:
        app.logger.info("Rebuilding RAG index from %d manuals on startup", len(manuals))
        result = build_manual_index()
        app.logger.info("RAG index built: %s", result)
    else:
        app.logger.warning("No manuals found in DATA_DIR on startup")
except Exception as e:
    app.logger.warning("RAG index build failed on startup: %s", e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
