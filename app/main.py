import json
from typing import List, Tuple

from openai import OpenAI

from app.config import EMBEDDING_MODEL, OPENAI_API_KEY, OPENAI_MODEL
from app.database import get_document_chunks_for_user, get_session_history


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
            current_len = sum(len(item) for item in current) + len(current)
        current.append(word)
        current_len += len(word) + 1

    if current:
        chunks.append(" ".join(current))

    return [chunk.strip() for chunk in chunks if chunk.strip()]


def cosine_similarity(a: List[float], b: List[float]) -> float:
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


def search_documents_by_query(user_id: int, query: str, limit: int = 4) -> List[str]:
    if not query.strip():
        return []

    try:
        query_embedding = create_embedding(query)
    except Exception:
        return []

    chunks = get_document_chunks_for_user(user_id)
    scored: List[Tuple[float, str]] = []
    for row in chunks:
        vector = json.loads(row["embedding"])
        score = cosine_similarity(query_embedding, vector)
        scored.append((score, row["chunk_text"]))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:limit]]


def build_system_prompt(context: List[str]) -> str:
    context_block = "\n\n".join(f"- {item}" for item in context[:4]) if context else "- No relevant knowledge base context found."
    return (
        "You are a helpful, professional AI assistant. Provide concise but useful answers. "
        "If the uploaded knowledge base is relevant, use it to ground your response. "
        "If context is missing or weak, say so clearly and answer from general knowledge.\n\n"
        f"Relevant knowledge base context:\n{context_block}"
    )


def generate_response(user_id: int, session_id: str, user_message: str, temperature: float = 0.7) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set.")

    context = search_documents_by_query(user_id, user_message)
    history = get_session_history(session_id, user_id)

    messages = [{"role": "system", "content": build_system_prompt(context)}]
    for item in history:
        messages.append({"role": item["role"], "content": item["content"]})
    messages.append({"role": "user", "content": user_message})

    client = OpenAI(api_key=OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=temperature,
    )

    reply = completion.choices[0].message.content
    if not reply:
        return "I’m sorry, I couldn’t generate a response."
    return reply
