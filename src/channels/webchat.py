"""
WebChat Channel — serves a beautiful single-page chat & project UI.

Renders markdown responses with full formatting support:
- Standard Chat Interface
- Project Management Interface (Plan, Logs, Status)
"""

from __future__ import annotations


def get_webchat_html() -> str:
    """Return the WebChat HTML page as a string."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦞 Wingman</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <!-- Marked.js for markdown parsing -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <!-- Highlight.js for code syntax highlighting -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/github-dark.min.css">
    <script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js"></script>
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-sidebar: #0f0f15;
            --bg-input: #1a1a2e;
            --bg-code: #0d1117;
            --border: #252538;
            --border-code: #30363d;
            --text-primary: #e4e4ef;
            --text-secondary: #8888a8;
            --text-code: #c9d1d9;
            --accent: #6366f1;
            --accent-glow: rgba(99, 102, 241, 0.25);
            --user-bubble: #1e1e3a;
            --assistant-bubble: #161625;
            --success: #34d399;
            --error: #f87171;
            --warning: #fbbf24;
            --table-border: #30363d;
            --table-row-alt: rgba(99, 102, 241, 0.04);
            --blockquote-border: #6366f1;
            --link-color: #818cf8;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            height: 100vh;
            display: flex;
            overflow: hidden;
        }

        /* Sidebar */
        .sidebar {
            width: 260px;
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }

        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .logo-icon { font-size: 24px; }
        .logo-text { font-weight: 700; font-size: 16px; color: var(--text-primary); }

        .sidebar-menu {
            flex: 1;
            padding: 16px;
            overflow-y: auto;
        }

        .menu-label {
            font-size: 11px;
            text-transform: uppercase;
            color: var(--text-secondary);
            margin-bottom: 8px;
            padding-left: 8px;
            font-weight: 600;
        }

        .menu-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            border-radius: 8px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s;
            font-size: 14px;
            margin-bottom: 4px;
        }

        .menu-item:hover {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-primary);
        }

        .menu-item.active {
            background: rgba(99, 102, 241, 0.1);
            color: var(--accent);
            font-weight: 500;
        }
        
        .project-list {
            margin-top: 20px;
        }

        .new-project-btn {
            width: 100%;
            padding: 10px;
            margin-top: 10px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            color: var(--text-primary);
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            transition: all 0.2s;
        }

        .new-project-btn:hover {
            border-color: var(--accent);
            color: var(--accent);
        }

        /* Main Content */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        /* Header */
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 24px;
            border-bottom: 1px solid var(--border);
            background: var(--bg-secondary);
            backdrop-filter: blur(20px);
            z-index: 10;
        }

        .status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: var(--text-secondary);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 8px rgba(52, 211, 153, 0.4);
            animation: pulse 2s infinite;
        }

        /* Chat View */
        #chat-view {
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        #chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            scroll-behavior: smooth;
        }

        /* Project View */
        #project-view {
            display: none;
            flex-direction: column;
            height: 100%;
            padding: 0;
            overflow: hidden;
        }
        
        .project-header {
            padding: 20px 30px;
            border-bottom: 1px solid var(--border);
            background: var(--bg-primary);
        }
        
        .project-title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 6px;
        }
        
        .project-meta {
            font-size: 13px;
            color: var(--text-secondary);
            display: flex;
            gap: 16px;
        }
        
        .project-grid {
            display: grid;
            grid-template-columns: 350px 1fr;
            height: 100%;
            overflow: hidden;
        }
        
        .project-plan {
            border-right: 1px solid var(--border);
            overflow-y: auto;
            padding: 20px;
            background: var(--bg-secondary);
        }
        
        .plan-step {
            padding: 12px 14px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .plan-step.active {
            border-color: var(--accent);
            background: rgba(99, 102, 241, 0.05);
        }
        
        .plan-step.completed { border-left: 3px solid var(--success); }
        .plan-step.in_progress { border-left: 3px solid var(--accent); }
        .plan-step.failed { border-left: 3px solid var(--error); }
        .plan-step.pending { border-left: 3px solid var(--text-secondary); }

        .step-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
        }
        
        .step-title { font-weight: 600; font-size: 14px; }
        .step-status { font-size: 11px; text-transform: uppercase; font-weight: 600; }
        
        .step-desc {
            font-size: 12px;
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .project-logs {
            padding: 20px;
            overflow-y: auto;
            background: #0d0d12;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
        }
        
        .log-entry {
            margin-bottom: 6px;
            color: var(--text-code);
            border-bottom: 1px solid #1a1a24;
            padding-bottom: 4px;
        }
        
        .log-timestamp { color: var(--text-secondary); margin-right: 8px; }

        .project-actions {
            padding: 16px 20px;
            border-top: 1px solid var(--border);
            background: var(--bg-secondary);
            display: flex;
            justify-content: flex-end;
        }
        
        .action-btn {
            padding: 10px 20px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-size: 13px;
        }
        
        .action-btn:hover { opacity: 0.9; }
        .action-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        /* Modal */
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.7);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 100;
        }
        
        .modal {
            background: var(--bg-secondary);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid var(--border);
            width: 500px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        
        .modal h3 { margin-bottom: 16px; font-size: 18px; }
        
        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; margin-bottom: 6px; font-size: 14px; color: var(--text-secondary); }
        .form-group input, .form-group textarea {
            width: 100%;
            padding: 10px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
        }
        
        .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }
        
        .btn-secondary {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
        }

        /* Message Styles (Shared with Chat) */
        .message {
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
            max-width: 850px;
            animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            margin-left: auto;
            flex-direction: row-reverse;
        }

        .avatar {
            width: 36px;
            height: 36px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            flex-shrink: 0;
            margin-top: 2px;
        }

        .avatar.user-avatar { background: linear-gradient(135deg, #6366f1, #8b5cf6); }
        .avatar.bot-avatar { background: linear-gradient(135deg, #f97316, #ef4444); }

        .bubble {
            border-radius: 16px;
            font-size: 14.5px;
            line-height: 1.7;
            max-width: 720px;
            word-break: break-word;
        }

        .bubble.user-bubble {
            padding: 14px 18px;
            background: var(--user-bubble);
            border: 1px solid var(--border);
            border-top-right-radius: 4px;
        }

        .bubble.bot-bubble {
            padding: 2px 18px 14px;
            background: var(--assistant-bubble);
            border: 1px solid var(--border);
            border-top-left-radius: 4px;
        }

        /* Common formatting similar to previous version... */
        .bubble h1, .bubble h2 { margin: 16px 0 8px; font-weight: 600; line-height: 1.3; }
        .bubble h1 { font-size: 20px; }
        .bubble h2 { font-size: 17px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
        .bubble p { margin: 8px 0; }
        .bubble pre { background: var(--bg-code); border: 1px solid var(--border-code); border-radius: 8px; padding: 12px; overflow-x: auto; margin: 10px 0; }
        .bubble code { font-family: 'JetBrains Mono', monospace; font-size: 13px; }
        
        /* Input Area (Chat) */
        .input-area {
            padding: 16px 24px 24px;
            border-top: 1px solid var(--border);
            background: var(--bg-secondary);
        }

        .input-row {
            display: flex;
            gap: 12px;
            max-width: 880px;
            margin: 0 auto;
        }

        #user-input {
            flex: 1;
            padding: 14px 18px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 14px;
            color: var(--text-primary);
            outline: none;
            resize: none;
            min-height: 48px;
            max-height: 200px;
        }
        
        #send-btn {
            padding: 12px 20px;
            background: var(--accent);
            border: none;
            border-radius: 14px;
            color: white;
            font-weight: 600;
            cursor: pointer;
        }
        
        /* Thinking */
        .thinking { display: flex; align-items: center; gap: 8px; padding: 12px 18px; color: var(--text-secondary); font-size: 13px; }
        .thinking-dots { display: flex; gap: 4px; }
        .thinking-dots span { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); animation: dotPulse 1.4s infinite; }
        .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
        .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes dotPulse { 0%, 100% { transform: scale(0.6); opacity: 0.4; } 50% { transform: scale(1); opacity: 1; } }

    </style>
</head>
<body>
    <!-- Sidebar -->
    <div class="sidebar">
        <div class="sidebar-header">
            <span class="logo-icon">🦞</span>
            <span class="logo-text">Wingman</span>
        </div>
        <div class="sidebar-menu">
            <div class="menu-label">Menu</div>
            <div class="menu-item active" onclick="switchView('chat')">💬 Chat</div>
            
            <div class="project-list">
                <div class="menu-label">Projects</div>
                <div id="projects-container">
                    <!-- Projects injected here -->
                </div>
                <button class="new-project-btn" onclick="showNewProjectModal()">+ New Project</button>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <header>
            <div class="status">
                <span class="status-dot" id="status-dot"></span>
                <span id="status-text">Connected</span>
            </div>
        </header>

        <!-- Chat View -->
        <div id="chat-view">
            <div id="chat-container">
                <div class="welcome" id="welcome" style="text-align:center; padding: 80px 20px;">
                    <h2 style="margin-bottom:10px;">Hello! How can I help?</h2>
                    <p style="color:var(--text-secondary);">Start a chat or create a project for complex tasks.</p>
                </div>
            </div>
            <div class="input-area">
                <div class="input-row">
                    <textarea id="user-input" placeholder="Type a message..." rows="1" onkeydown="handleKeyDown(event)"></textarea>
                    <button id="send-btn" onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>

        <!-- Project View -->
        <div id="project-view">
            <div class="project-header">
                <div class="project-title" id="p-title">Project Name</div>
                <div class="project-meta">
                    <span id="p-status">Status: Planning</span>
                    <span id="p-path">/workspace/projects/foo</span>
                </div>
            </div>
            <div class="project-grid">
                <div class="project-plan" id="p-plan">
                    <!-- Steps injected here -->
                </div>
                <div style="display:flex; flex-direction:column; height:100%; overflow:hidden;">
                     <div class="project-logs" id="p-logs">
                        <!-- Logs injected here -->
                        <div class="log-entry">Waiting for action...</div>
                    </div>
                    <div class="project-actions">
                        <button class="action-btn" id="run-step-btn" onclick="runNextStep()">Run Next Step ▶</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- New Project Modal -->
    <div class="modal-overlay" id="new-project-modal">
        <div class="modal">
            <h3>Create New Project</h3>
            <div class="form-group">
                <label>Project Name</label>
                <input type="text" id="np-name" placeholder="e.g., snake-game">
            </div>
            <div class="form-group">
                <label>Description / Prompt</label>
                <textarea id="np-prompt" rows="4" placeholder="Describe what you want to build..."></textarea>
            </div>
            <div class="modal-actions">
                <button class="btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="action-btn" onclick="createProject()">Create Project</button>
            </div>
        </div>
    </div>

    <script>
        // Use basic markdown rendering for chat
        marked.setOptions({ gfm: true, breaks: true });

        let ws = null;
        let sessionId = null;
        let currentProjectName = null;

        function connect() {
            const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${location.host}/ws`);

            ws.onopen = () => {
                setStatus('Connected', true);
                ws.send(JSON.stringify({ type: 'init', session_id: sessionId }));
                // Fetch projects list
                ws.send(JSON.stringify({ type: 'project_list' }));
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };

            ws.onclose = () => {
                setStatus('Disconnected', false);
                setTimeout(connect, 3000);
            };
        }

        function handleMessage(data) {
            switch (data.type) {
                case 'session':
                    sessionId = data.session_id;
                    if(data.project) updateProjectView(data.project);
                    break;
                case 'response':
                    removeThinking();
                    addMessage(data.content, 'bot');
                    break;
                case 'thinking':
                    if (data.status) showThinking(); else removeThinking();
                    break;
                case 'project_list':
                    renderProjectList(data.projects);
                    break;
                case 'project_update':
                    updateProjectView(data.project);
                    if(data.message) addLog(data.message);
                    break;
                case 'error':
                    alert("Error: " + data.content);
                    break;
            }
        }

        /* --- UI Logic --- */

        function switchView(view) {
            document.getElementById('chat-view').style.display = view === 'chat' ? 'flex' : 'none';
            document.getElementById('project-view').style.display = view === 'project' ? 'flex' : 'none';
            
            // Highlight menu items
            document.querySelectorAll('.menu-item').forEach(el => el.classList.remove('active'));
            if(view === 'chat') {
                document.querySelector('.menu-item').classList.add('active'); // Assume first is chat
            }
        }

        function showNewProjectModal() {
            document.getElementById('new-project-modal').style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('new-project-modal').style.display = 'none';
        }

        function createProject() {
            const name = document.getElementById('np-name').value;
            const prompt = document.getElementById('np-prompt').value;
            if(!name || !prompt) return;
            
            ws.send(JSON.stringify({
                type: 'project_create',
                name: name,
                prompt: prompt
            }));
            
            currentProjectName = name;
            closeModal();
            switchView('project');
        }

        function loadProject(name) {
            currentProjectName = name;
            ws.send(JSON.stringify({
                type: 'project_load',
                name: name
            }));
            switchView('project');
        }
        
        function runNextStep() {
            if(!currentProjectName) return;
            ws.send(JSON.stringify({ type: 'project_next' }));
            addLog("Requested next step...");
        }

        function renderProjectList(projects) {
            const container = document.getElementById('projects-container');
            container.innerHTML = '';
            projects.forEach(p => {
                const div = document.createElement('div');
                div.className = 'menu-item';
                div.textContent = `📁 ${p}`;
                div.onclick = () => loadProject(p);
                container.appendChild(div);
            });
        }

        function updateProjectView(project) {
            document.getElementById('p-title').textContent = project.name;
            document.getElementById('p-status').textContent = 'Status: ' + project.status.toUpperCase();
            document.getElementById('p-path').textContent = project.workspace_path;
            
            // Render Plan
            const planContainer = document.getElementById('p-plan');
            planContainer.innerHTML = '';
            
            if(project.plan.length === 0) {
                 planContainer.innerHTML = '<div style="color:var(--text-secondary); text-align:center; margin-top:20px;">Planning in progress...</div>';
            } else {
                project.plan.forEach(step => {
                    const div = document.createElement('div');
                    div.className = `plan-step ${step.status}`;
                    div.innerHTML = `
                        <div class="step-header">
                            <span class="step-title">Step ${step.id}: ${step.title}</span> #
                            <span class="step-status">${step.status}</span>
                        </div>
                        <div class="step-desc">${step.description}</div>
                    `;
                    planContainer.appendChild(div);
                });
            }
            
            // Render History/Logs
            const logContainer = document.getElementById('p-logs');
            logContainer.innerHTML = ''; // Full redraw for simplicity
            project.history.forEach(entry => {
                const div = document.createElement('div');
                div.className = 'log-entry';
                div.textContent = `> ${entry}`;
                logContainer.appendChild(div);
            });
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        function addLog(msg) {
             const logContainer = document.getElementById('p-logs');
             const div = document.createElement('div');
             div.className = 'log-entry';
             div.textContent = `> ${msg}`;
             logContainer.appendChild(div);
             logContainer.scrollTop = logContainer.scrollHeight;
        }

        /* --- Chat Logic --- */
        
        function sendMessage() {
            const input = document.getElementById('user-input');
            const text = input.value.trim();
            if (!text || !ws) return;
            
            document.getElementById('welcome').style.display = 'none';
            addMessage(text, 'user');
            ws.send(JSON.stringify({ type: 'message', content: text }));
            input.value = '';
        }

        function addMessage(text, role) {
            const container = document.getElementById('chat-container');
            const div = document.createElement('div');
            div.className = `message ${role}`;
            
            const avatar = role === 'user' ? '👤' : '🦞';
            const bubbleClass = role === 'user' ? 'user-bubble' : 'bot-bubble';
            
            // Simple Render
            const html = role === 'bot' ? marked.parse(text) : text;
            
            div.innerHTML = `
                <div class="avatar ${role}-avatar">${avatar}</div>
                <div class="bubble ${bubbleClass}">${html}</div>
            `;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
            
             // Highlight code
            div.querySelectorAll('pre code').forEach(block => {
                hljs.highlightElement(block);
            });
        }

        function showThinking() {
            // Only for chat view
            if(document.getElementById('chat-view').style.display === 'none') return;
            
            const container = document.getElementById('chat-container');
            if(document.getElementById('thinking')) return;
            
            const div = document.createElement('div');
            div.id = 'thinking';
            div.className = 'message';
            div.innerHTML = `
                <div class="avatar bot-avatar">🦞</div>
                <div class="thinking">
                    <div class="thinking-dots"><span></span><span></span><span></span></div>
                    Thinking...
                </div>
            `;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }

        function removeThinking() {
            const el = document.getElementById('thinking');
            if (el) el.remove();
        }

        function setStatus(text, connected) {
            document.getElementById('status-text').textContent = text;
            document.getElementById('status-dot').style.background = connected ? 'var(--success)' : 'var(--error)';
        }

        function handleKeyDown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        }

        connect();
    </script>
</body>
</html>'''
