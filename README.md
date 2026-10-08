<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Production AI Assistant</title>
    <style>
      :root{
        --bg:#09111d;--panel:#101b2d;--panel-2:#16253a;--text:#edf3ff;--muted:#a9b8cc;--primary:#7aa2ff;--secondary:#57d38d;--danger:#ff6b6b;--border:rgba(160,185,255,0.18)
      }
      *{box-sizing:border-box} body{margin:0;background:linear-gradient(180deg,#07111a,#0e1c2d 100%);color:var(--text);font-family:Arial,sans-serif}
      .auth-shell{max-width:480px;margin:80px auto 24px;padding:24px;border:1px solid var(--border);border-radius:16px;background:rgba(16,27,45,0.96);box-shadow:0 30px 90px rgba(0,0,0,.35)}
      .auth-shell h2{margin:0 0 20px;font-size:1.5rem}
      .form-grid{display:flex;flex-direction:column;gap:12px}.form-grid input{padding:12px 14px;border-radius:10px;border:1px solid var(--border);background:var(--panel-2);color:var(--text)}
      .button-row{display:flex;gap:10px;margin-top:6px}.button-row button{flex:1;border:none;border-radius:10px;padding:12px 16px;font-weight:700;cursor:pointer}
      .primary{background:linear-gradient(135deg,var(--primary),#4f46e5);color:white}.secondary{background:rgba(122,162,255,.1);color:var(--text);border:1px solid var(--border)}
      .status{margin-top:12px;color:var(--muted);font-size:.9rem}
      .layout{display:grid;grid-template-columns:240px 1fr;min-height:calc(100vh - 120px)}
      .sidebar{background:rgba(10,16,28,.9);border-right:1px solid var(--border);padding:16px}
      .brand{font-weight:700;font-size:1.15rem;margin-bottom:16px}
      .panel{margin-top:16px;padding:12px;border:1px solid var(--border);border-radius:10px;background:rgba(22,37,58,.7)}
      .session-list{display:flex;flex-direction:column;gap:8px;margin-top:12px} .session-item{background:rgba(255,255,255,.03);color:var(--text);border:1px solid var(--border);padding:10px;border-radius:10px;cursor:pointer;text-align:left}
      .session-item.active{border-color:rgba(122,162,255,.82);background:rgba(122,162,255,.1)}
      .main{display:flex;flex-direction:column;height:100%}
      .header{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid var(--border);background:rgba(16,27,45,.85)}
      .chat-area{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px}
      .message{max-width:72%;padding:12px 14px;border-radius:14px;line-height:1.5;white-space:pre-wrap}
      .message.user{margin-left:auto;background:rgba(122,162,255,.18);border:1px solid rgba(122,162,255,.35)}
      .message.assistant{margin-right:auto;background:rgba(87,211,141,.08);border:1px solid rgba(87,211,141,.3)}
      .composer{display:flex;gap:10px;padding:16px 20px;border-top:1px solid var(--border);background:rgba(16,27,45,.85)}
      textarea{flex:1;resize:vertical;min-height:54px;max-height:180px;padding:12px 14px;border-radius:12px;border:1px solid var(--border);background:var(--panel-2);color:var(--text)}
      .send-btn{border:none;border-radius:12px;padding:12px 18px;font-weight:700;background:linear-gradient(135deg,var(--primary),#4f46e5);color:white;cursor:pointer}
      .logout{padding:10px 12px;border-radius:10px;border:1px solid var(--border);background:rgba(255,107,107,.08);color:var(--text);cursor:pointer}
      .hidden{display:none!important}
    </style>
  </head>
  <body>
    <div id="authView" class="auth-shell">
      <h2>AI Assistant Login</h2>
      <div class="form-grid">
        <input id="username" placeholder="Username" />
        <input id="password" type="password" placeholder="Password" />
      </div>
      <div class="button-row">
        <button class="primary" id="loginBtn">Login</button>
        <button class="secondary" id="registerBtn">Register</button>
      </div>
      <div class="status" id="authStatus">Use your credentials to continue.</div>
    </div>

    <div id="appView" class="layout hidden">
      <aside class="sidebar">
        <div class="brand">AI Assistant</div>
        <button class="secondary" id="newChatBtn" style="width:100%;margin-bottom:8px;">+ New chat</button>
        <button class="logout" id="logoutBtn" style="width:100%;">Log out</button>

        <div class="panel">
          <div style="font-weight:700;margin-bottom:8px;">Sessions</div>
          <div class="session-list" id="sessionList"></div>
        </div>

        <div class="panel">
          <div style="font-weight:700;margin-bottom:8px;">Docs</div>
          <input type="file" id="documentInput" class="hidden" />
          <button class="secondary" id="documentUploadBtn" style="width:100%;">Upload document</button>
          <div class="session-list" id="documentList"></div>
        </div>
      </aside>

      <main class="main">
        <div class="header">
          <div id="chatTitle">New conversation</div>
          <div style="color:var(--secondary);font-weight:700">● Ready</div>
        </div>
        <div class="chat-area" id="chatArea"></div>
        <div class="composer">
          <textarea id="promptInput" placeholder="Ask a question..."></textarea>
          <button class="send-btn" id="sendBtn">Send</button>
        </div>
      </main>
    </div>

    <script>
      const authView = document.getElementById('authView');
      const appView = document.getElementById('appView');
      const usernameInput = document.getElementById('username');
      const passwordInput = document.getElementById('password');
      const authStatus = document.getElementById('authStatus');
      const sessionList = document.getElementById('sessionList');
      const documentList = document.getElementById('documentList');
      const chatArea = document.getElementById('chatArea');
      const promptInput = document.getElementById('promptInput');
      const chatTitle = document.getElementById('chatTitle');

      const state = { token: localStorage.getItem('token') || '', sessionId: null, sessions: [], documents: [] };

      function setAuthVisible(isLoggedIn) {
        authView.classList.toggle('hidden', isLoggedIn);
        appView.classList.toggle('hidden', !isLoggedIn);
      }

      function getAuthHeaders() {
        return { 'Authorization': `Bearer ${state.token}` };
      }

      function appendMessage(role, text) {
        const msg = document.createElement('div');
        msg.className = `message ${role}`;
        msg.textContent = text;
        chatArea.appendChild(msg);
        chatArea.scrollTop = chatArea.scrollHeight;
      }

      async function authRequest(endpoint, body) {
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(body)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Authentication failed');
        return data;
      }

      async function login() {
        try {
          const data = await authRequest('/api/auth/login', {
            username: usernameInput.value.trim(),
            password: passwordInput.value
          });
          state.token = data.access_token;
          localStorage.setItem('token', data.access_token);
          setAuthVisible(true);
          authStatus.textContent = 'Logged in';
          await loadSessions();
          await loadDocuments();
          startNewChat();
        } catch (error) {
          authStatus.textContent = error.message;
        }
      }

      async function register() {
        try {
          const data = await authRequest('/api/auth/register', {
            username: usernameInput.value.trim(),
            password: passwordInput.value
          });
          state.token = data.access_token;
          localStorage.setItem('token', data.access_token);
          setAuthVisible(true);
          authStatus.textContent = 'Registered successfully';
          await loadSessions();
          await loadDocuments();
          startNewChat();
        } catch (error) {
          authStatus.textContent = error.message;
        }
      }

      function logout() {
        state.token = '';
        localStorage.removeItem('token');
        setAuthVisible(false);
        usernameInput.value = '';
        passwordInput.value = '';
      }

      async function loadSessions() {
        const res = await fetch('/api/sessions', { headers: getAuthHeaders() });
        const data = await res.json();
        state.sessions = data.sessions || [];
        renderSessions();
      }

      async function loadDocuments() {
        const res = await fetch('/api/documents', { headers: getAuthHeaders() });
        const data = await res.json();
        state.documents = data.documents || [];
        renderDocuments();
      }

      function renderSessions() {
        sessionList.innerHTML = '';
        state.sessions.forEach((session) => {
          const button = document.createElement('button');
          button.className = `session-item ${session.id === state.sessionId ? 'active' : ''}`;
          button.textContent = session.title || 'Untitled conversation';
          button.onclick = () => openSession(session.id);
          sessionList.appendChild(button);
        });
      }

      function renderDocuments() {
        documentList.innerHTML = '';
        if (!state.documents.length) {
          const item = document.createElement('div');
          item.style.color = 'var(--muted)';
          item.textContent = 'No documents yet';
          documentList.appendChild(item);
          return;
        }
        state.documents.forEach((doc) => {
          const item = document.createElement('div');
          item.textContent = doc.title;
          documentList.appendChild(item);
        });
      }

      async function openSession(sessionId) {
        state.sessionId = sessionId;
        chatArea.innerHTML = '';
        const res = await fetch(`/api/sessions/${sessionId}/history`, { headers: getAuthHeaders() });
        const data = await res.json();
        (data.messages || []).forEach((msg) => appendMessage(msg.role, msg.content));
        chatTitle.textContent = 'Conversation';
        renderSessions();
      }

      function startNewChat() {
        state.sessionId = null;
        chatArea.innerHTML = '';
        appendMessage('assistant', 'Hello! I am ready to help. Ask me anything.');
        chatTitle.textContent = 'New conversation';
      }

      async function sendMessage() {
        const text = promptInput.value.trim();
        if (!text) return;
        appendMessage('user', text);
        promptInput.value = '';

        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
          body: JSON.stringify({ session_id: state.sessionId, message: text })
        });

        const data = await res.json();
        if (!res.ok) {
          appendMessage('assistant', `Error: ${data.detail || 'Request failed'}`);
          return;
        }

        state.sessionId = data.session_id;
        appendMessage('assistant', data.reply);
        await loadSessions();
        renderSessions();
      }

      async function uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', file.name);
        const res = await fetch('/api/documents/upload', {
          method: 'POST',
          headers: getAuthHeaders(),
          body: formData
        });
        const data = await res.json();
        if (!res.ok) {
          authStatus.textContent = data.detail || 'Upload failed';
          return;
        }
        authStatus.textContent = data.message || 'Upload complete';
        await loadDocuments();
      }

      document.getElementById('loginBtn').addEventListener('click', login);
      document.getElementById('registerBtn').addEventListener('click', register);
      document.getElementById('logoutBtn').addEventListener('click', logout);
      document.getElementById('sendBtn').addEventListener('click', sendMessage);
      document.getElementById('newChatBtn').addEventListener('click', startNewChat);
      document.getElementById('documentUploadBtn').addEventListener('click', () => document.getElementById('documentInput').click());
      document.getElementById('documentInput').addEventListener('change', (event) => {
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

      if (state.token) {
        setAuthVisible(true);
        loadSessions();
        loadDocuments();
        startNewChat();
      } else {
        setAuthVisible(false);
      }
    </script>
  </body>
</html>
