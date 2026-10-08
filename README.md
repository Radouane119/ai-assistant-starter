# AI Assistant Starter

A simple AI assistant starter built with FastAPI and the OpenAI API. It includes:

- A chat API endpoint
- A basic web UI for testing the assistant
- Environment-based configuration
- Easy setup and extension points for adding memory, RAG, or tools

## Features

- FastAPI backend
- OpenAI-compatible chat completion integration
- Simple chat UI served from the app
- Health check endpoint
- Ready for extension with memory, document retrieval, and function calling

## Quick start

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file from the example:

   ```bash
   cp .env.example .env
   ```

4. Add your OpenAI API key to `.env`:

   ```env
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   ```

5. Run the app:

   ```bash
   uvicorn app.main:app --reload
   ```

6. Open the app in your browser:

   - http://localhost:8000

## API endpoints

### Health check

```bash
curl http://localhost:8000/api/health
```

### Chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello! Can you help me build an AI assistant?"}]
  }'
```

## Project structure

```text
.
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   └── schemas.py
├── static/
│   └── index.html
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── .venv/
```

## Customization ideas

- Add persistent conversation history with PostgreSQL or SQLite
- Add document retrieval (RAG) using embeddings and a vector database
- Add tool calling for web search, database queries, or custom APIs
- Add authentication and user sessions
- Replace the basic HTML UI with React or Next.js

## License

This project is open-sourced under the MIT license.
