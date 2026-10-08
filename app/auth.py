import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT 'New conversation',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES chat_sessions(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                document_id INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                embedding TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
            """
        )

        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id)")


def create_user(username: str, password_hash: str) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        return {"id": cursor.lastrowid, "username": username}


def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


def create_session(user_id: int, title: str = "New conversation") -> str:
    import uuid

    session_id = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (session_id, user_id, title),
        )
    return session_id


def list_sessions_for_user(user_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_session_for_user(session_id: str, user_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM chat_sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        ).fetchone()


def get_session_history(session_id: str, user_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT role, content, created_at FROM chat_messages WHERE session_id = ? AND user_id = ? ORDER BY id ASC",
            (session_id, user_id),
        ).fetchall()
    return [dict(row) for row in rows]


def add_message(session_id: str, user_id: int, role: str, content: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_messages (session_id, user_id, role, content, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (session_id, user_id, role, content),
        )
        conn.execute(
            "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        )


def save_document(user_id: int, title: str, content: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO documents (user_id, title, content, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (user_id, title, content),
        )
        document_id = cursor.lastrowid
    return int(document_id)


def list_documents_for_user(user_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at FROM documents WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_document_chunks_for_document(document_id: int, user_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM document_chunks WHERE user_id = ? AND document_id = ?",
            (user_id, document_id),
        )


def store_document_chunks(user_id: int, document_id: int, chunks: List[str], embeddings: List[List[float]]) -> None:
    if len(chunks) != len(embeddings):
        return
    with get_connection() as conn:
        for chunk, embedding in zip(chunks, embeddings):
            conn.execute(
                "INSERT INTO document_chunks (user_id, document_id, chunk_text, embedding, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (user_id, document_id, chunk, json.dumps(embedding)),
            )


def get_document_chunks_for_user(user_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, document_id, chunk_text, embedding FROM document_chunks WHERE user_id = ?",
            (user_id,),
        ).fetchall()


def get_or_create_session_for_user(user_id: int, session_id: Optional[str]) -> str:
    if session_id:
        existing = get_session_for_user(session_id, user_id)
        if existing:
            return session_id
    return create_session(user_id)


def ensure_session_title(session_id: str, user_id: int, title: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE chat_sessions SET title = ? WHERE id = ? AND user_id = ?",
            (title, session_id, user_id),
        )
