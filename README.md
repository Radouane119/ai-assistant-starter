<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Advanced AI Assistant</title>
    <style>
      :root {
        --bg: #0b1020;
        --panel: #121a2a;
        --panel-alt: #192437;
        --text: #edf2ff;
        --muted: #a9b7d0;
        --primary: #7c9cff;
        --secondary: #4ade80;
        --danger: #f87171;
        --border: rgba(170, 190, 255, 0.18);
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: linear-gradient(180deg, #090d1b 0%, #10192d 100%);
        color: var(--text);
      }

      .layout {
        display: grid;
        grid-template-columns: 260px 1fr;
        min-height: 100vh;
      }

      .sidebar {
        background: rgba(10, 16, 28, 0.9);
        border-right: 1px solid var(--border);
        padding: 1rem;
      }

      .brand {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 1rem;
      }

      .sessions {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        margin-top: 1rem;
      }

      .session-item {
        background: rgba(18, 26, 42, 0.9);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 0.7rem 0.8rem;
        cursor: pointer;
        color: var(--text);
      }

      .session-item.active {
        border-color: rgba(124, 156, 255, 0.8);
        background: rgba(124, 156, 255, 0.1);
      }

      .main {
        display: flex;
        flex-direction: column;
        height: 100vh;
      }

      .header {
        padding: 1rem 1.2rem;
        border-bottom: 1px solid var(--border);
        background: rgba(14, 21, 35, 0.75);
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .header h1 {
        margin: 0;
        font-size: 1.2rem;
      }

      .new-chat-btn, .upload-btn, .send-btn {
        border: none;
        border-radius: 10px;
        font-weight: 700;
        cursor: pointer;
      }

      .new-chat-btn, .upload-btn {
        padding: 0.7rem 0.9rem;
        background: rgba(124, 156, 255, 0.12);
        color: var(--text);
        border: 1px solid var(--border);
      }

      .send-btn {
        background: linear-gradient(135deg, var(--primary), #4f46e5);
        color: white;
        padding: 0.9rem 1.2rem;
      }

      .chat-area {
        flex: 1;
        overflow-y: auto;
        padding: 1.2rem;
      }

      .message {
        max-width: 75%;
        margin-bottom: 1rem;
        padding: 0.9rem 1rem;
        border-radius: 14px;
        line-height: 1.5;
        white-space: pre-wrap;
      }

      .message.user {
        margin-left: auto;
        background: rgba(124, 156, 255, 0.18);
        border: 1px solid rgba(124, 156, 255, 0.35);
      }

      .message.assistant {
        margin-right: auto;
        background: rgba(74, 222, 128, 0.08);
        border: 1px solid rgba(74, 222, 128, 0.3);
      }

      .composer {
        border-top: 1px solid var(--border);
        padding: 1rem 1.2rem;
        background: rgba(14, 21, 35, 0.8);
      }

      .composer-inner {
        display: flex;
        gap: 0.75rem;
      }

      textarea {
        flex: 1;
        min-height: 58px;
        max-height: 160px;
        resize: vertical;
        padding: 0.9rem 1rem;
        border-radius: 12px;
        background: rgba(25, 36, 55, 0.9);
        color: var(--text);
        border: 1px solid var(--border);
      }

      .document-panel {
        margin-top: 1rem;
        padding: 0.9rem 1rem;
        border: 1px solid var(--border);
        border-radius: 10px;
        background: rgba(18, 26, 42, 0.9);
      }

      .document-panel h3 {
        margin: 0 0 0.8rem;
        font-size: 1rem;
      }

      .document-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        color: var(--muted);
        font-size: 0.9rem;
      }

      .document-list div {
        padding: 0.5rem 0.7rem;
        border-radius: 8px;
        background: rgba(255,255,255,0.02);
      }

      .status {
        color: var(--muted);
        font-size: 0.82rem;
        padding: 0.5rem 0 0;
      }
    </style>
  </head>
  <body>
    <div class="layout">
      <aside class="sidebar">
        <div class="brand">AI Assistant</div>
        <button class="new-chat-btn" id="newChatBtn">+ New chat</button>

        <div class="sessions" id="sessionsList"></div>

        <div class="document-panel">
          <h3>Knowledge base</h3>
          <input type="file" id="documentInput" style="display:none;" />
          <button class="upload-btn" id="documentUploadBtn">Upload document</button>
          <div class="document-list" id="documentList"></div>
        </div>
      </aside>

      <main class="main">
        <div class="header">
          <h1 id="chatTitle">Conversation</h1>
          <span id="onlineStatus" style="color: var(--secondary);">● Ready</span>
        </div>

        <div class="chat-area" id="chatArea"></div>

        <div class="composer">
          <div class="composer-inner">
            <textarea id="promptInput" placeholder="Ask a question or start a conversation..."></textarea>
            <button class="send-btn" id="sendBtn">Send</button>
          </div>
          <div class="status" id="statusText">Ready</div>
        </div>
      </main>
    </div>

    <script>
      const state = {
        sessionId: null,
        sessions: [],
        documents: [],
      };

      const chatArea = document.getElementById('chatArea');
      const promptInput = document.getElementById('promptInput');
      const sessionsList = document.getElementById('sessionsList');
      const documentList = document.getElementById('documentList');
      const sendBtn = document.getElementById('sendBtn');
      const newChatBtn = document.getElementById('newChatBtn');
      const statusText = document.getElementById('statusText');
      const documentInput = document.getElementById('documentInput');
      const documentUploadBtn = document.getElementById('documentUploadBtn');

      function appendMessage(role, content) {
        const message = document.createElement('div');
        message.className = `message ${role}`;
        message.textContent = content;
        chatArea.appendChild(message);
        chatArea.scrollTop = chatArea.scrollHeight;
      }

      function renderSessions() {
        sessionsList.innerHTML = '';
        state.sessions.forEach((session) => {
          const btn = document.createElement('button');
          btn.className = `session-item ${session.id === state.sessionId ? 'active' : ''}`;
          btn.textContent = session.title || 'Untitled conversation';
          btn.onclick = () => loadSession(session.id);
          sessionsList.appendChild(btn);
        });
      }

      function renderDocuments() {
        documentList.innerHTML = '';
        if (!state.documents.length) {
          const item = document.createElement('div');
          item.textContent = 'No documents uploaded yet.';
          documentList.appendChild(item);
          return;
        }

        state.documents.forEach((doc) => {
          const item = document.createElement('div');
          item.textContent = doc.title;
          documentList.appendChild(item);
        });
      }

      async function loadSessions() {
        const response = await fetch('/api/sessions');
        const data = await response.json();
        state.sessions = data.sessions || [];
        if (!state.sessionId && state.sessions.length) {
          loadSession(state.sessions[0].id);
        }
        renderSessions();
      }

      async function loadDocuments() {
        const response = await fetch('/api/documents');
        const data = await response.json();
        state.documents = data.documents || [];
        renderDocuments();
      }

      async function loadSession(sessionId) {
        state.sessionId = sessionId;
        chatArea.innerHTML = '';
        const response = await fetch(`/api/sessions/${sessionId}/history`);
        const data = await response.json();
        const messages = data.messages || [];
        for (const msg of messages) {
          appendMessage(msg.role, msg.content);
        }
        renderSessions();
      }

      async function createNewSession() {
        state.sessionId = null;
        chatArea.innerHTML = '';
        appendMessage('assistant', 'New conversation started. Ask me anything.');
        await loadSessions();
      }

      async function sendMessage() {
        const text = promptInput.value.trim();
        if (!text) return;

        if (!state.sessionId) {
          state.sessionId = null;
        }

        appendMessage('user', text);
        promptInput.value = '';
        sendBtn.disabled = true;
        statusText.textContent = 'Thinking...';

        try {
          const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: state.sessionId, message: text }),
          });

          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.detail || 'Request failed');
          }

          state.sessionId = data.session_id;
          appendMessage('assistant', data.reply);
          statusText.textContent = 'Ready';
          await loadSessions();
        } catch (error) {
          appendMessage('assistant', `Error: ${error.message}`);
          statusText.textContent = 'Error';
        } finally {
          sendBtn.disabled = false;
        }
      }

      async function uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', file.name);

        statusText.textContent = 'Uploading document...';
        try {
          const response = await fetch('/api/documents/upload', {
            method: 'POST',
            body: formData,
          });

          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.detail || 'Upload failed');
          }

          statusText.textContent = data.message || 'Document uploaded';
          await loadDocuments();
        } catch (error) {
          statusText.textContent = `Upload error: ${error.message}`;
        }
      }

      sendBtn.addEventListener('click', sendMessage);
      newChatBtn.addEventListener('click', createNewSession);
      documentUploadBtn.addEventListener('click', () => documentInput.click());
      documentInput.addEventListener('change', (event) => {
        const file = event.target.files && event.target.files[0];
        if (file) uploadDocument(file);
        event.target.value = '';
      });

      promptInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault();
          sendMessage();
        }
      });

      loadSessions();
      loadDocuments();
      appendMessage('assistant', 'Hello! I can answer questions and use uploaded documents as context.');
    </script>
  </body>
</html>
