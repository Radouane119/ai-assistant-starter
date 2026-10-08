import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.schemas import ChatRequest, ChatResponse

app = FastAPI(
    title="AI Assistant Starter",
    description="A simple AI assistant built with FastAPI and OpenAI",
    version="0.1.0",
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "AI Assistant is running"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages were provided.")

    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not set. Add it to your .env file.",
        )

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        payload = [{"role": "system", "content": "You are a helpful AI assistant. Be concise, clear, and practical."}]
        payload.extend({"role": message.role, "content": message.content} for message in request.messages)

        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=payload,
            temperature=request.temperature,
        )

        reply = completion.choices[0].message.content
        if not reply:
            raise HTTPException(status_code=500, detail="The model returned an empty response.")

        return ChatResponse(reply=reply)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI request failed: {str(exc)}") from exc
