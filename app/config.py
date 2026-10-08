import json
import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple

from openai import OpenAI

from app.config import DATABASE_PATH, EMBEDDING_MODEL, OPENAI_API_KEY, OPENAI_MODEL


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                embedding TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
            """
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id)"
        )


def create_session(title: str = "New conversation") -> str:
    import uuid

    session_id = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_sessions (id, title, created_at, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (session_id, title),
        )
    return session_id


def get_session_history(session_id: str) -> List[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_message(session_id: str, role: str, content: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (session_id, role, content),
        )
        conn.execute(
            "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,),
        )


def list_sessions() -> List[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM chat_sessions
            ORDER BY updated_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def split_text(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    if not text.strip():
        return []

    words = text.split()
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for word in words:
        if current_len + len(word) + 1 > chunk_size and current:
            chunks.append(" ".join(current))
            overlap_words = current[-max(1, overlap // 5):]
            current = overlap_words[:]
            current_len = sum(len(p) for p in current) + len(current) - 1
        current.append(word)
        current_len += len(word) + 1

    if current:
        chunks.append(" ".join(current))

    return [chunk.strip() for chunk in chunks if chunk.strip()]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def create_embedding(text: str) -> List[float]:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def save_document(title: str, content: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO documents (title, content, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (title, content),
        )
        document_id = cursor.lastrowid

    chunks = split_text(content)
    if not chunks:
        return document_id

    for chunk in chunks:
        embedding = create_embedding(chunk)
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO document_chunks (document_id, chunk_text, embedding, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (document_id, chunk, json.dumps(embedding)),
            )

    return document_id


def list_documents() -> List[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, content, created_at FROM documents ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def search_documents(query: str, limit: int = 4) -> List[str]:
    if not query.strip():
        return []

    try:
        query_embedding = create_embedding(query)
    except ValueError:
        return []
    except Exception:
        return []

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, document_id, chunk_text, embedding FROM document_chunks"
        ).fetchall()

    scored: List[Tuple[float, str]] = []
    for row in rows:
        vector = json.loads(row["embedding"])
        score = _cosine_similarity(query_embedding, vector)
        scored.append((score, row["chunk_text"]))

    scored.sort(key=lambda item: item[0], reverse=True)
    results = [chunk for _, chunk in scored[:limit]]
    return results


def build_system_prompt(context: List[str]) -> str:
    context_block = "\n\n".join(f"- {item}" for item in context[:4]) if context else "- No relevant knowledge base context found."
    return (
        "You are a helpful AI assistant. "
        "Answer clearly and use the provided context when it is relevant. "
        "If the useful information is not in the context, say so and provide a practical answer.\n\n"
        f"Relevant context from uploaded documents:\n{context_block}"
    )


def generate_response(session_id: str, user_message: str) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set.")

    context = search_documents(user_message)
    history = get_session_history(session_id)
    messages = [{"role": "system", "content": build_system_prompt(context)}]

    for item in history:
        messages.append({"role": item["role"], "content": item["content"]})

    messages.append({"role": "user", "content": user_message})

    client = OpenAI(api_key=OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.7,
    )

    reply = completion.choices[0].message.content
    if not reply:
        return "I’m sorry, I couldn’t generate a response."
    return reply


def get_or_create_session(session_id: Optional[str]) -> str:
    if session_id:
        with get_connection() as conn:
            exists = conn.execute(
                "SELECT id FROM chat_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if exists:
            return session_id
    return create_session()


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
