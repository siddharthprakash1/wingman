"""
WebChat Channel — Futuristic AI Assistant Interface.

A sleek, cyberpunk-inspired chat UI with:
- File upload with progress indicators
- Real-time streaming responses
- Tool execution visualization
- Processing status feedback
"""

from __future__ import annotations


def get_webchat_html() -> str:
    """Return the futuristic WebChat HTML page."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WINGMAN // AI NEURAL INTERFACE</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;900&family=Rajdhani:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/tokyo-night-dark.min.css">
    <script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js"></script>
    <style>
        :root {
            --bg-void: #000000;
            --bg-deep: #030308;
            --bg-surface: #0a0a12;
            --bg-elevated: #0f0f1a;
            --bg-card: #12121f;
            --bg-input: #0d0d18;
            
            --border-dim: rgba(99, 102, 241, 0.1);
            --border-subtle: rgba(99, 102, 241, 0.2);
            --border-accent: rgba(99, 102, 241, 0.4);
            --border-glow: rgba(99, 102, 241, 0.6);
            
            --text-primary: #e8e8f0;
            --text-secondary: #6a6a8a;
            --text-dim: #404060;
            
            --accent-primary: #6366f1;
            --accent-secondary: #818cf8;
            --accent-glow: rgba(99, 102, 241, 0.5);
            
            --cyan: #22d3ee;
            --cyan-glow: rgba(34, 211, 238, 0.4);
            --magenta: #e879f9;
            --magenta-glow: rgba(232, 121, 249, 0.4);
            --green: #4ade80;
            --green-glow: rgba(74, 222, 128, 0.4);
            --orange: #fb923c;
            --red: #f87171;
            
            --gradient-accent: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
            --gradient-cyber: linear-gradient(135deg, #06b6d4 0%, #6366f1 50%, #a855f7 100%);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Rajdhani', sans-serif;
            background: var(--bg-void);
            color: var(--text-primary);
            height: 100vh;
            overflow: hidden;
            position: relative;
        }

        .bg-grid {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: 
                linear-gradient(rgba(99, 102, 241, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(99, 102, 241, 0.03) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: gridMove 20s linear infinite;
            pointer-events: none;
            z-index: 0;
        }

        @keyframes gridMove {
            0% { transform: translate(0, 0); }
            100% { transform: translate(50px, 50px); }
        }

        .scanlines {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 0, 0, 0.1) 2px, rgba(0, 0, 0, 0.1) 4px);
            pointer-events: none;
            z-index: 1000;
            opacity: 0.3;
        }

        .app-container {
            display: flex;
            height: 100vh;
            position: relative;
            z-index: 1;
        }

        /* Sidebar */
        .sidebar {
            width: 280px;
            background: var(--bg-deep);
            border-right: 1px solid var(--border-subtle);
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .sidebar::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 1px;
            background: var(--gradient-cyber);
        }

        .sidebar-header {
            padding: 24px 20px;
            border-bottom: 1px solid var(--border-dim);
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-icon {
            width: 44px;
            height: 44px;
            background: var(--gradient-accent);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 0 20px var(--accent-glow);
            animation: logoPulse 3s ease-in-out infinite;
        }

        @keyframes logoPulse {
            0%, 100% { box-shadow: 0 0 20px var(--accent-glow); }
            50% { box-shadow: 0 0 35px var(--accent-glow), 0 0 60px rgba(99, 102, 241, 0.2); }
        }

        .logo-text {
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            font-size: 18px;
            letter-spacing: 3px;
            background: var(--gradient-cyber);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .logo-subtitle {
            font-size: 10px;
            color: var(--text-dim);
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-top: 2px;
        }

        .nav-section {
            padding: 20px 16px;
            flex: 1;
            overflow-y: auto;
        }

        .nav-label {
            font-family: 'Orbitron', sans-serif;
            font-size: 10px;
            color: var(--text-dim);
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 12px;
            padding-left: 8px;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border-radius: 8px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 4px;
            border: 1px solid transparent;
            position: relative;
        }

        .nav-item::before {
            content: '';
            position: absolute;
            left: 0; top: 0; bottom: 0;
            width: 3px;
            background: var(--gradient-accent);
            transform: scaleY(0);
            transition: transform 0.2s ease;
        }

        .nav-item:hover {
            background: rgba(99, 102, 241, 0.08);
            color: var(--text-primary);
            border-color: var(--border-dim);
        }

        .nav-item.active {
            background: rgba(99, 102, 241, 0.12);
            color: var(--accent-secondary);
            border-color: var(--border-accent);
        }

        .nav-item.active::before { transform: scaleY(1); }

        .nav-icon { font-size: 18px; width: 24px; text-align: center; }

        .status-bar {
            padding: 16px 20px;
            border-top: 1px solid var(--border-dim);
            background: var(--bg-surface);
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 12px;
            color: var(--text-secondary);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--green);
            box-shadow: 0 0 10px var(--green-glow);
            animation: statusPulse 2s ease-in-out infinite;
        }

        .status-dot.disconnected {
            background: var(--red);
            box-shadow: 0 0 10px rgba(248, 113, 113, 0.4);
        }

        @keyframes statusPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* Main Content */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg-deep);
            position: relative;
        }

        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 28px;
            border-bottom: 1px solid var(--border-dim);
            background: rgba(3, 3, 8, 0.8);
            backdrop-filter: blur(20px);
        }

        .header-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 14px;
            letter-spacing: 3px;
            color: var(--text-secondary);
        }

        .header-actions { display: flex; gap: 12px; }

        .header-btn {
            padding: 8px 16px;
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 6px;
            color: var(--text-secondary);
            font-family: 'Rajdhani', sans-serif;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .header-btn.active {
            border-color: var(--green);
            color: var(--green);
            box-shadow: 0 0 10px rgba(74, 222, 128, 0.2);
        }

        .header-btn:hover {
            border-color: var(--accent-primary);
            color: var(--accent-secondary);
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.2);
        }

        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 30px;
            scroll-behavior: smooth;
        }

        .chat-container::-webkit-scrollbar { width: 6px; }
        .chat-container::-webkit-scrollbar-track { background: var(--bg-surface); }
        .chat-container::-webkit-scrollbar-thumb { background: var(--border-subtle); border-radius: 3px; }

        /* Welcome Screen */
        .welcome-screen {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
            padding: 40px;
        }

        .welcome-icon {
            width: 100px;
            height: 100px;
            background: var(--gradient-cyber);
            border-radius: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 50px;
            margin-bottom: 30px;
            box-shadow: 0 0 60px var(--accent-glow);
            animation: welcomePulse 4s ease-in-out infinite;
        }

        @keyframes welcomePulse {
            0%, 100% { transform: scale(1); box-shadow: 0 0 60px var(--accent-glow); }
            50% { transform: scale(1.05); box-shadow: 0 0 80px var(--accent-glow), 0 0 120px rgba(99, 102, 241, 0.2); }
        }

        .welcome-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: 4px;
            margin-bottom: 12px;
            background: var(--gradient-cyber);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .welcome-subtitle {
            font-size: 16px;
            color: var(--text-secondary);
            max-width: 500px;
            line-height: 1.6;
            margin-bottom: 40px;
        }

        .quick-actions { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; }

        .quick-action {
            padding: 16px 24px;
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            font-weight: 500;
        }

        .quick-action:hover {
            border-color: var(--accent-primary);
            color: var(--text-primary);
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(99, 102, 241, 0.15);
        }

        .quick-action-icon { font-size: 20px; }

        /* Messages */
        .message {
            display: flex;
            gap: 16px;
            margin-bottom: 28px;
            animation: messageSlide 0.4s ease-out;
            max-width: 900px;
        }

        @keyframes messageSlide {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user { flex-direction: row-reverse; margin-left: auto; }

        .avatar {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
            position: relative;
        }

        .avatar.user-avatar {
            background: linear-gradient(135deg, #06b6d4, #0891b2);
            box-shadow: 0 0 20px var(--cyan-glow);
        }

        .avatar.bot-avatar {
            background: var(--gradient-accent);
            box-shadow: 0 0 20px var(--accent-glow);
        }

        .message-content { flex: 1; min-width: 0; }

        .message-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }

        .message-sender {
            font-family: 'Orbitron', sans-serif;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: var(--text-dim);
        }

        .message-time { font-size: 11px; color: var(--text-dim); }

        .bubble {
            padding: 18px 22px;
            border-radius: 16px;
            font-size: 15px;
            line-height: 1.7;
            position: relative;
        }

        .bubble.user-bubble {
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(8, 145, 178, 0.1));
            border: 1px solid rgba(6, 182, 212, 0.3);
            border-top-right-radius: 4px;
        }

        .bubble.bot-bubble {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-top-left-radius: 4px;
        }

        /* Markdown Styles */
        .bubble h1, .bubble h2, .bubble h3 {
            font-family: 'Orbitron', sans-serif;
            margin: 20px 0 12px;
            letter-spacing: 1px;
        }
        .bubble h1 { font-size: 20px; color: var(--cyan); }
        .bubble h2 { font-size: 17px; color: var(--accent-secondary); border-bottom: 1px solid var(--border-dim); padding-bottom: 8px; }
        .bubble h3 { font-size: 15px; color: var(--magenta); }
        .bubble p { margin: 10px 0; }
        .bubble pre {
            background: var(--bg-void);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 16px;
            overflow-x: auto;
            margin: 14px 0;
            position: relative;
        }
        .bubble pre::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: var(--gradient-cyber);
            border-radius: 10px 10px 0 0;
        }
        .bubble code { font-family: 'JetBrains Mono', monospace; font-size: 13px; }
        .bubble :not(pre) > code {
            background: rgba(99, 102, 241, 0.15);
            padding: 2px 8px;
            border-radius: 4px;
            color: var(--accent-secondary);
        }
        .bubble ul, .bubble ol { margin: 12px 0; padding-left: 24px; }
        .bubble li { margin: 6px 0; }
        .bubble blockquote {
            border-left: 3px solid var(--accent-primary);
            padding-left: 16px;
            margin: 14px 0;
            color: var(--text-secondary);
            font-style: italic;
        }
        .bubble a { color: var(--cyan); text-decoration: none; }
        .bubble a:hover { border-bottom: 1px solid var(--cyan); }
        .bubble table { width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 14px; }
        .bubble th, .bubble td { padding: 10px 14px; border: 1px solid var(--border-dim); text-align: left; }
        .bubble th { background: var(--bg-surface); font-family: 'Orbitron', sans-serif; font-size: 11px; letter-spacing: 1px; text-transform: uppercase; color: var(--accent-secondary); }
        .bubble tr:nth-child(even) { background: rgba(99, 102, 241, 0.03); }

        /* Progress/Status Indicators */
        .progress-container {
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 20px;
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            margin: 10px 0;
        }

        .progress-header {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .progress-spinner {
            width: 24px;
            height: 24px;
            border: 3px solid var(--border-subtle);
            border-top-color: var(--cyan);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .progress-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 12px;
            letter-spacing: 2px;
            color: var(--cyan);
        }

        .progress-status {
            font-size: 13px;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .progress-bar-container {
            height: 4px;
            background: var(--bg-surface);
            border-radius: 2px;
            overflow: hidden;
        }

        .progress-bar {
            height: 100%;
            background: var(--gradient-cyber);
            border-radius: 2px;
            transition: width 0.3s ease;
            animation: progressPulse 2s ease-in-out infinite;
        }

        .progress-bar.indeterminate {
            width: 30%;
            animation: indeterminate 1.5s ease-in-out infinite;
        }

        @keyframes indeterminate {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(400%); }
        }

        @keyframes progressPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        .progress-steps {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 8px;
        }

        .progress-step {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 12px;
            color: var(--text-dim);
        }

        .progress-step.active { color: var(--cyan); }
        .progress-step.done { color: var(--green); }

        .progress-step-icon {
            width: 18px;
            height: 18px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
        }

        .progress-step.active .progress-step-icon {
            border-color: var(--cyan);
            animation: stepPulse 1s ease-in-out infinite;
        }

        .progress-step.done .progress-step-icon {
            background: var(--green);
            border-color: var(--green);
            color: var(--bg-void);
        }

        @keyframes stepPulse {
            0%, 100% { box-shadow: 0 0 0 0 var(--cyan-glow); }
            50% { box-shadow: 0 0 0 6px transparent; }
        }

        /* Thinking Animation */
        .thinking-container {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 16px 20px;
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            animation: thinkingPulse 2s ease-in-out infinite;
        }

        @keyframes thinkingPulse {
            0%, 100% { border-color: var(--border-subtle); }
            50% { border-color: var(--accent-primary); box-shadow: 0 0 20px rgba(99, 102, 241, 0.1); }
        }

        .thinking-orb {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: var(--gradient-cyber);
            position: relative;
            animation: orbSpin 2s linear infinite;
        }

        .thinking-orb::before {
            content: '';
            position: absolute;
            inset: 3px;
            background: var(--bg-card);
            border-radius: 50%;
        }

        .thinking-orb::after {
            content: '';
            position: absolute;
            top: 2px;
            left: 50%;
            transform: translateX(-50%);
            width: 6px;
            height: 6px;
            background: var(--cyan);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--cyan);
        }

        @keyframes orbSpin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .thinking-text {
            font-family: 'Orbitron', sans-serif;
            font-size: 12px;
            letter-spacing: 2px;
            color: var(--text-secondary);
        }

        .thinking-dots {
            display: flex;
            gap: 4px;
            margin-left: auto;
        }

        .thinking-dots span {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--accent-primary);
            animation: dotBounce 1.4s ease-in-out infinite;
        }

        .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
        .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes dotBounce {
            0%, 100% { transform: scale(0.8); opacity: 0.4; }
            50% { transform: scale(1.2); opacity: 1; }
        }

        /* Tool Badge */
        .tool-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: rgba(74, 222, 128, 0.1);
            border: 1px solid rgba(74, 222, 128, 0.3);
            border-radius: 6px;
            font-size: 12px;
            color: var(--green);
            margin: 8px 4px 8px 0;
            font-family: 'JetBrains Mono', monospace;
        }

        /* Input Area */
        .input-area {
            padding: 20px 30px 28px;
            background: var(--bg-surface);
            border-top: 1px solid var(--border-dim);
            position: relative;
        }

        .input-area::before {
            content: '';
            position: absolute;
            top: 0; left: 30px; right: 30px;
            height: 1px;
            background: var(--gradient-cyber);
            opacity: 0.5;
        }

        .input-wrapper { max-width: 900px; margin: 0 auto; }

        .input-row {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }

        .input-box {
            flex: 1;
            position: relative;
        }

        #user-input {
            width: 100%;
            padding: 16px 20px;
            padding-right: 50px;
            background: var(--bg-input);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            color: var(--text-primary);
            font-family: 'Rajdhani', sans-serif;
            font-size: 15px;
            outline: none;
            resize: none;
            min-height: 54px;
            max-height: 200px;
            transition: all 0.3s ease;
        }

        #user-input:focus {
            border-color: var(--accent-primary);
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.15);
        }

        #user-input::placeholder { color: var(--text-dim); }
        #user-input:disabled { opacity: 0.5; cursor: not-allowed; }

        .input-actions {
            position: absolute;
            right: 12px;
            bottom: 10px;
            display: flex;
            gap: 8px;
        }

        .input-btn {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            border: 1px solid var(--border-subtle);
            background: var(--bg-card);
            color: var(--text-secondary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            transition: all 0.2s;
        }

        .input-btn:hover {
            border-color: var(--accent-primary);
            color: var(--accent-secondary);
            transform: scale(1.05);
        }

        .input-btn.upload-btn:hover {
            border-color: var(--cyan);
            color: var(--cyan);
        }

        #send-btn {
            width: 54px;
            height: 54px;
            border-radius: 14px;
            border: none;
            background: var(--gradient-accent);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px var(--accent-glow);
        }

        #send-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 30px var(--accent-glow);
        }

        #send-btn:active { transform: scale(0.95); }
        #send-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

        /* File Upload Area */
        .file-upload-area {
            display: none;
            margin-bottom: 16px;
            padding: 24px;
            background: var(--bg-card);
            border: 2px dashed var(--border-subtle);
            border-radius: 12px;
            text-align: center;
            transition: all 0.3s;
            cursor: pointer;
        }

        .file-upload-area.active { display: block; }

        .file-upload-area.dragover {
            border-color: var(--cyan);
            background: rgba(34, 211, 238, 0.05);
        }

        .file-upload-icon { font-size: 40px; margin-bottom: 12px; }
        .file-upload-text { font-size: 14px; color: var(--text-secondary); margin-bottom: 8px; }
        .file-upload-hint { font-size: 12px; color: var(--text-dim); }

        .file-list {
            margin-top: 16px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }

        .file-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            font-size: 13px;
        }

        .file-item.uploading {
            border-color: var(--cyan);
            animation: fileUploadPulse 1s ease-in-out infinite;
        }

        @keyframes fileUploadPulse {
            0%, 100% { box-shadow: 0 0 0 0 var(--cyan-glow); }
            50% { box-shadow: 0 0 10px var(--cyan-glow); }
        }

        .file-item.done { border-color: var(--green); }
        .file-item.error { border-color: var(--red); }

        .file-item-remove {
            cursor: pointer;
            color: var(--red);
            font-size: 14px;
        }

        #file-input { display: none; }

        /* Toast Notifications */
        .toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1001;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .toast {
            padding: 14px 20px;
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
            animation: toastSlide 0.3s ease-out;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }

        .toast.success { border-color: var(--green); }
        .toast.error { border-color: var(--red); }
        .toast.info { border-color: var(--cyan); }

        @keyframes toastSlide {
            from { opacity: 0; transform: translateX(100px); }
            to { opacity: 1; transform: translateX(0); }
        }

        /* Modal */
        .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 100;
        }

        .modal-overlay.active { display: flex; }

        .modal {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            padding: 28px;
            width: 480px;
            max-width: 90vw;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.5);
            position: relative;
        }

        .modal::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: var(--gradient-cyber);
            border-radius: 16px 16px 0 0;
        }

        .modal-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 18px;
            letter-spacing: 2px;
            margin-bottom: 20px;
            color: var(--text-primary);
        }

        .form-group { margin-bottom: 18px; }

        .form-label {
            display: block;
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .form-input {
            width: 100%;
            padding: 12px 16px;
            background: var(--bg-input);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            color: var(--text-primary);
            font-family: 'Rajdhani', sans-serif;
            font-size: 15px;
            transition: all 0.2s;
        }

        .form-input:focus {
            outline: none;
            border-color: var(--accent-primary);
        }

        .modal-actions {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            margin-top: 24px;
        }

        .btn {
            padding: 10px 20px;
            border-radius: 8px;
            font-family: 'Rajdhani', sans-serif;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-secondary {
            background: transparent;
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
        }

        .btn-secondary:hover {
            border-color: var(--text-secondary);
            color: var(--text-primary);
        }

        .btn-primary {
            background: var(--gradient-accent);
            border: none;
            color: white;
        }

        .btn-primary:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 20px var(--accent-glow);
        }

        @media (max-width: 768px) {
            .sidebar { display: none; }
            .chat-container { padding: 20px; }
            .input-area { padding: 16px; }
        }
    </style>
</head>
<body>
    <div class="bg-grid"></div>
    <div class="scanlines"></div>
    <div class="toast-container" id="toast-container"></div>

    <div class="app-container">
        <div class="sidebar">
            <div class="sidebar-header">
                <div class="logo">
                    <div class="logo-icon">🦞</div>
                    <div>
                        <div class="logo-text">WINGMAN</div>
                        <div class="logo-subtitle">Neural Interface v2.0</div>
                    </div>
                </div>
            </div>
            <div class="nav-section">
                <div class="nav-label">Navigation</div>
                <div class="nav-item active" onclick="switchView('chat')">
                    <span class="nav-icon">💬</span><span>Chat Interface</span>
                </div>
                <div class="nav-item" onclick="toggleFileUpload()">
                    <span class="nav-icon">📁</span><span>Upload Documents</span>
                </div>
                <div class="nav-label" style="margin-top: 24px;">Projects</div>
                <div id="projects-container"></div>
                <div class="nav-item" onclick="showNewProjectModal()" style="color: var(--accent-secondary);">
                    <span class="nav-icon">➕</span><span>New Project</span>
                </div>
            </div>
            <div class="status-bar">
                <div class="status-indicator">
                    <div class="status-dot" id="status-dot"></div>
                    <span id="status-text">CONNECTED</span>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div class="header">
                <div class="header-title">// NEURAL LINK ACTIVE</div>
                <div class="header-actions">
                    <button class="header-btn active" id="autopilot-btn" onclick="toggleAutoPilot()"><span>🚀</span> Auto-Pilot: ON</button>
                    <button class="header-btn" onclick="runNextStep()"><span>▶</span> Run Step</button>
                    <button class="header-btn" onclick="clearChat()"><span>🗑️</span> Clear</button>
                    <button class="header-btn" onclick="toggleFileUpload()"><span>📎</span> Upload</button>
                </div>
            </div>

            <div class="chat-container" id="chat-container">
                <div class="welcome-screen" id="welcome-screen">
                    <div class="welcome-icon">🦞</div>
                    <h1 class="welcome-title">WINGMAN ONLINE</h1>
                    <p class="welcome-subtitle">Advanced AI assistant ready for coding, research, document analysis, and web automation.</p>
                    <div class="quick-actions">
                        <div class="quick-action" onclick="quickAction('Help me write code')">
                            <span class="quick-action-icon">💻</span><span>Write Code</span>
                        </div>
                        <div class="quick-action" onclick="quickAction('Search the web for')">
                            <span class="quick-action-icon">🔍</span><span>Web Search</span>
                        </div>
                        <div class="quick-action" onclick="toggleFileUpload()">
                            <span class="quick-action-icon">📄</span><span>Analyze Document</span>
                        </div>
                        <div class="quick-action" onclick="quickAction('Extract data from')">
                            <span class="quick-action-icon">🔬</span><span>Extract Data</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="input-area">
                <div class="input-wrapper">
                    <div class="file-upload-area" id="file-upload-area">
                        <div class="file-upload-icon">📁</div>
                        <div class="file-upload-text">Drag & drop files or click to browse</div>
                        <div class="file-upload-hint">PDF, TXT, MD, HTML, JSON, CSV supported</div>
                        <div class="file-list" id="file-list"></div>
                    </div>
                    <input type="file" id="file-input" multiple accept=".pdf,.txt,.md,.html,.htm,.json,.csv">

                    <div class="input-row">
                        <div class="input-box">
                            <textarea id="user-input" placeholder="Enter your message..." rows="1" onkeydown="handleKeyDown(event)" oninput="autoResize(this)"></textarea>
                            <div class="input-actions">
                                <button class="input-btn upload-btn" onclick="toggleFileUpload()" title="Upload Files">📎</button>
                            </div>
                        </div>
                        <button id="send-btn" onclick="sendMessage()">➤</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="project-modal">
        <div class="modal">
            <div class="modal-title">// NEW PROJECT</div>
            <div class="form-group">
                <label class="form-label">Project Name</label>
                <input type="text" class="form-input" id="project-name" placeholder="e.g., my-app">
            </div>
            <div class="form-group">
                <label class="form-label">Description</label>
                <textarea class="form-input" id="project-desc" rows="4" placeholder="Describe what you want to build..."></textarea>
            </div>
            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn btn-primary" onclick="createProject()">Create Project</button>
            </div>
        </div>
    </div>

    <script>
        marked.setOptions({ gfm: true, breaks: true });

        let ws = null;
        let sessionId = null;
        let uploadedFiles = [];
        let isAutoPilot = true; // Auto-Pilot enabled by default
        let recentlyUploadedFiles = [];  // Track files uploaded in this session
        let isProcessing = false;
        let currentProgressId = null;

        function connect() {
            const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${location.host}/ws`);

            ws.onopen = () => {
                setStatus('CONNECTED', true);
                ws.send(JSON.stringify({ type: 'init', session_id: sessionId }));
                ws.send(JSON.stringify({ type: 'project_list' }));
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };

            ws.onclose = () => {
                setStatus('DISCONNECTED', false);
                setTimeout(connect, 3000);
            };

            ws.onerror = () => setStatus('ERROR', false);
        }

        function handleMessage(data) {
            switch (data.type) {
                case 'session':
                    sessionId = data.session_id;
                    break;
                case 'response':
                    removeProgress();
                    removeThinking();
                    addMessage(data.content, 'bot');
                    setProcessing(false);
                    break;
                case 'thinking':
                    if (data.status) {
                        showThinking(data.message || 'Processing your request...');
                    } else {
                        removeThinking();
                    }
                    break;
                case 'progress':
                    updateProgress(data);
                    break;
                case 'tool_call':
                    updateThinkingStatus(`Executing: ${data.tool}`);
                    break;
                case 'project_list':
                    renderProjects(data.projects);
                    break;
                case 'project_update':
                    // Update current project state in UI
                    console.log('Project update received:', data);
                    if (data.project) {
                        updateProjectUI(data.project);
                        if (data.message) {
                            showToast(`📁 ${data.message}`, 'info');
                        }
                    }
                    closeModal();  // Close the create modal if open
                    break;
                case 'file_uploading':
                    showFileProgress(data.filename, 'uploading');
                    break;
                case 'file_processing':
                    showFileProgress(data.filename, 'processing', data.step);
                    break;
                case 'file_uploaded':
                    showFileProgress(data.filename, 'done');
                    showToast(`✅ "${data.filename}" indexed: ${data.chunks} chunks`, 'success');
                    // Track recently uploaded files for context
                    recentlyUploadedFiles.push({
                        filename: data.filename,
                        chunks: data.chunks,
                        characters: data.characters,
                        time: Date.now()
                    });
                    console.log('File uploaded, recentlyUploadedFiles:', recentlyUploadedFiles);
                    setTimeout(() => removeFileProgress(data.filename), 2000);
                    
                    // Check if there's a pending message waiting for uploads to complete
                    if (pendingUploads > 0) {
                        pendingUploads--;
                        if (pendingUploads === 0 && pendingMessage) {
                            console.log('All uploads complete, sending pending message:', pendingMessage);
                            showThinking('Analyzing request...');
                            actualSendMessage(pendingMessage);
                            pendingMessage = null;
                        }
                    }
                    break;
                case 'error':
                    removeProgress();
                    removeThinking();
                    showToast(`❌ ${data.content}`, 'error');
                    setProcessing(false);
                    break;
            }
        }

        function setStatus(text, connected) {
            document.getElementById('status-text').textContent = text;
            document.getElementById('status-dot').classList.toggle('disconnected', !connected);
        }

        function setProcessing(processing) {
            isProcessing = processing;
            document.getElementById('user-input').disabled = processing;
            document.getElementById('send-btn').disabled = processing;
        }

        // Toast Notifications
        function showToast(message, type = 'info') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `<span>${message}</span>`;
            container.appendChild(toast);
            setTimeout(() => toast.remove(), 5000);
        }

        // Progress Indicator
        function showProgress(title, steps = []) {
            removeProgress();
            const container = document.getElementById('chat-container');
            
            const div = document.createElement('div');
            div.id = 'progress-indicator';
            div.className = 'message';
            
            let stepsHtml = '';
            if (steps.length > 0) {
                stepsHtml = `<div class="progress-steps">
                    ${steps.map((step, i) => `
                        <div class="progress-step ${i === 0 ? 'active' : ''}" data-step="${i}">
                            <div class="progress-step-icon">${i === 0 ? '◉' : '○'}</div>
                            <span>${step}</span>
                        </div>
                    `).join('')}
                </div>`;
            }
            
            div.innerHTML = `
                <div class="avatar bot-avatar">🦞</div>
                <div class="message-content">
                    <div class="progress-container">
                        <div class="progress-header">
                            <div class="progress-spinner"></div>
                            <span class="progress-title">${title}</span>
                        </div>
                        <div class="progress-bar-container">
                            <div class="progress-bar indeterminate"></div>
                        </div>
                        <div class="progress-status" id="progress-status">Initializing...</div>
                        ${stepsHtml}
                    </div>
                </div>
            `;
            
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }

        function updateProgress(data) {
            const statusEl = document.getElementById('progress-status');
            if (statusEl && data.message) {
                statusEl.textContent = data.message;
            }
            
            if (data.step !== undefined) {
                document.querySelectorAll('.progress-step').forEach((el, i) => {
                    el.classList.remove('active', 'done');
                    if (i < data.step) el.classList.add('done');
                    else if (i === data.step) el.classList.add('active');
                    
                    const icon = el.querySelector('.progress-step-icon');
                    if (i < data.step) icon.textContent = '✓';
                    else if (i === data.step) icon.textContent = '◉';
                    else icon.textContent = '○';
                });
            }
            
            if (data.percent !== undefined) {
                const bar = document.querySelector('.progress-bar');
                if (bar) {
                    bar.classList.remove('indeterminate');
                    bar.style.width = data.percent + '%';
                }
            }
        }

        function removeProgress() {
            const el = document.getElementById('progress-indicator');
            if (el) el.remove();
        }

        // File Progress
        function showFileProgress(filename, status, step = '') {
            let item = document.querySelector(`.file-item[data-file="${filename}"]`);
            
            if (!item) {
                const list = document.getElementById('file-list');
                item = document.createElement('div');
                item.className = 'file-item';
                item.dataset.file = filename;
                list.appendChild(item);
            }
            
            item.classList.remove('uploading', 'done', 'error');
            
            if (status === 'uploading') {
                item.classList.add('uploading');
                item.innerHTML = `<span class="progress-spinner" style="width:16px;height:16px;border-width:2px;"></span><span>Uploading ${filename}...</span>`;
            } else if (status === 'processing') {
                item.classList.add('uploading');
                item.innerHTML = `<span class="progress-spinner" style="width:16px;height:16px;border-width:2px;"></span><span>${step || 'Processing'} ${filename}...</span>`;
            } else if (status === 'done') {
                item.classList.add('done');
                item.innerHTML = `<span>✅</span><span>${filename}</span>`;
            } else if (status === 'error') {
                item.classList.add('error');
                item.innerHTML = `<span>❌</span><span>${filename}</span>`;
            }
        }

        function removeFileProgress(filename) {
            const item = document.querySelector(`.file-item[data-file="${filename}"]`);
            if (item) item.remove();
        }

        // Thinking Animation
        function showThinking(message = 'Processing...') {
            const container = document.getElementById('chat-container');
            let thinkingEl = document.getElementById('thinking');
            
            if (!thinkingEl) {
                thinkingEl = document.createElement('div');
                thinkingEl.id = 'thinking';
                thinkingEl.className = 'message';
                thinkingEl.innerHTML = `
                    <div class="avatar bot-avatar">🦞</div>
                    <div class="message-content">
                        <div class="thinking-container">
                            <div class="thinking-orb"></div>
                            <span class="thinking-text" id="thinking-status">PROCESSING</span>
                            <div class="thinking-dots"><span></span><span></span><span></span></div>
                        </div>
                    </div>
                `;
                container.appendChild(thinkingEl);
                container.scrollTop = container.scrollHeight;
            }
        }

        function updateThinkingStatus(message) {
            const statusEl = document.getElementById('thinking-status');
            if (statusEl) statusEl.textContent = message.toUpperCase();
        }

        function removeThinking() {
            const el = document.getElementById('thinking');
            if (el) el.remove();
        }

        // Track pending uploads
        let pendingUploads = 0;
        let pendingMessage = null;
        
        // Chat Functions
        function sendMessage() {
            const input = document.getElementById('user-input');
            const text = input.value.trim();
            if (!text || !ws || isProcessing) return;

            document.getElementById('welcome-screen').style.display = 'none';
            
            // Handle file uploads first - if uploading, queue the message
            if (uploadedFiles.length > 0) {
                pendingUploads = uploadedFiles.length;
                pendingMessage = text;  // Save message to send after uploads complete
                uploadedFiles.forEach(file => {
                    showFileProgress(file.name, 'uploading');
                    sendFile(file);
                });
                uploadedFiles = [];
                hideFileUpload();
                input.value = '';
                addMessage(text, 'user');
                setProcessing(true);
                showThinking('Uploading and processing files...');
                return;  // Don't send message yet - wait for uploads
            }

            addMessage(text, 'user');
            setProcessing(true);
            showThinking('Analyzing request...');
            
            actualSendMessage(text);
            input.value = '';
            input.style.height = 'auto';
        }
        
        function actualSendMessage(text) {
            // Build message with context about recently uploaded files
            let messageContent = text;
            
            // Check for recently uploaded files (within last 5 minutes)
            const fiveMinutesAgo = Date.now() - (5 * 60 * 1000);
            const recentFiles = recentlyUploadedFiles.filter(f => f.time > fiveMinutesAgo);
            
            // Also detect document-related keywords
            const docKeywords = /\b(pdf|document|file|uploaded|attachment|the doc)\b/i;
            const mentionsDoc = docKeywords.test(text);
            
            if (recentFiles.length > 0) {
                const fileList = recentFiles.map(f => `"${f.filename}"`).join(', ');
                messageContent = `[Context: The user recently uploaded these documents to the knowledge base: ${fileList}. You MUST use the search_knowledge tool to answer questions about these documents.]\n\nUser question: ${text}`;
                console.log('Sending message with context:', messageContent);
            } else if (mentionsDoc) {
                // User mentions document but no recent uploads - tell them to check knowledge base
                messageContent = `[Context: The user is asking about a document. Use list_knowledge to check what's available, then search_knowledge to find relevant content.]\n\nUser question: ${text}`;
                console.log('Sending message with doc hint:', messageContent);
            }
            
            ws.send(JSON.stringify({ type: 'message', content: messageContent }));
        }

        function addMessage(text, role) {
            const container = document.getElementById('chat-container');
            const div = document.createElement('div');
            div.className = `message ${role}`;

            const avatar = role === 'user' ? '👤' : '🦞';
            const sender = role === 'user' ? 'YOU' : 'WINGMAN';
            const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const html = role === 'bot' ? marked.parse(text) : text.replace(/\\n/g, '<br>');

            div.innerHTML = `
                <div class="avatar ${role}-avatar">${avatar}</div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-sender">${sender}</span>
                        <span class="message-time">${time}</span>
                    </div>
                    <div class="bubble ${role}-bubble">${html}</div>
                </div>
            `;

            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
            div.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
        }

        function clearChat() {
            const container = document.getElementById('chat-container');
            container.innerHTML = '';
            const welcome = document.getElementById('welcome-screen');
            welcome.style.display = 'flex';
            container.appendChild(welcome);
        }

        function quickAction(prompt) {
            document.getElementById('user-input').value = prompt + ' ';
            document.getElementById('user-input').focus();
            document.getElementById('welcome-screen').style.display = 'none';
        }

        function switchView(view) {
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            event.currentTarget.classList.add('active');
        }

        // File Upload
        function toggleFileUpload() {
            const area = document.getElementById('file-upload-area');
            area.classList.toggle('active');
            if (area.classList.contains('active')) {
                document.getElementById('welcome-screen').style.display = 'none';
            }
        }

        function hideFileUpload() {
            document.getElementById('file-upload-area').classList.remove('active');
        }

        const fileUploadArea = document.getElementById('file-upload-area');
        const fileInput = document.getElementById('file-input');

        fileUploadArea.addEventListener('click', (e) => {
            if (e.target === fileUploadArea || e.target.classList.contains('file-upload-icon') || 
                e.target.classList.contains('file-upload-text') || e.target.classList.contains('file-upload-hint')) {
                fileInput.click();
            }
        });

        fileUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileUploadArea.classList.add('dragover');
        });

        fileUploadArea.addEventListener('dragleave', () => fileUploadArea.classList.remove('dragover'));

        fileUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            fileUploadArea.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });

        fileInput.addEventListener('change', () => handleFiles(fileInput.files));

        function handleFiles(files) {
            for (const file of files) {
                if (!uploadedFiles.find(f => f.name === file.name)) {
                    uploadedFiles.push(file);
                }
            }
            updateFileList();
        }

        function updateFileList() {
            const list = document.getElementById('file-list');
            list.innerHTML = '';
            uploadedFiles.forEach((file, index) => {
                const item = document.createElement('div');
                item.className = 'file-item';
                item.innerHTML = `
                    <span>📄 ${file.name}</span>
                    <span class="file-item-remove" onclick="removeFile(${index})">✕</span>
                `;
                list.appendChild(item);
            });
        }

        function removeFile(index) {
            uploadedFiles.splice(index, 1);
            updateFileList();
        }

        function sendFile(file) {
            const reader = new FileReader();
            reader.onload = () => {
                const base64 = reader.result.split(',')[1];
                ws.send(JSON.stringify({
                    type: 'file_upload',
                    filename: file.name,
                    content: base64,
                    mime_type: file.type
                }));
            };
            reader.readAsDataURL(file);
        }

        // Projects
        let currentProject = null;
        
        function renderProjects(projects) {
            const container = document.getElementById('projects-container');
            container.innerHTML = '';
            projects.forEach(name => {
                const item = document.createElement('div');
                item.className = 'nav-item';
                item.innerHTML = `<span class="nav-icon">📁</span><span>${name}</span>`;
                item.onclick = () => loadProject(name);
                container.appendChild(item);
            });
        }
        
        function updateProjectUI(project) {
            currentProject = project;
            console.log('Updating project UI:', project);
            
            // Show project status in chat
            const statusMsg = `**Project: ${project.name}**\n` +
                `- Phase: ${project.phase}\n` +
                `- Status: ${project.status}\n` +
                (project.current_task ? `- Current Task: ${project.current_task}\n` : '') +
                (project.tasks ? `- Tasks: ${project.completed_tasks || 0}/${project.tasks.length} completed` : '');
            
            addMessage(statusMsg, 'bot');
            
            // Refresh project list
            ws.send(JSON.stringify({ type: 'project_list' }));

            // Auto-Pilot Logic
            if (isAutoPilot && ['planning', 'coding', 'reviewing'].includes(project.status.toLowerCase())) {
                 updateThinkingStatus(`Auto-Pilot: Running next step in 3s...`);
                 setTimeout(() => {
                     if (isAutoPilot && currentProject && currentProject.name === project.name) {
                         ws.send(JSON.stringify({ type: 'project_next' }));
                     }
                 }, 3000);
            }


        }


        function toggleAutoPilot() {
            isAutoPilot = !isAutoPilot;
            const btn = document.getElementById('autopilot-btn');
            if (btn) {
                btn.style.borderColor = isAutoPilot ? 'var(--green)' : 'var(--border-subtle)';
                btn.style.color = isAutoPilot ? 'var(--green)' : 'var(--text-secondary)';
                btn.innerHTML = isAutoPilot ? '🚀 Auto-Pilot: ON' : '🚀 Auto-Pilot: OFF';
            }
            showToast(`Auto-Pilot ${isAutoPilot ? 'Enabled' : 'Disabled'}`, isAutoPilot ? 'success' : 'info');
            
            if (isAutoPilot && currentProject) {
                 ws.send(JSON.stringify({ type: 'project_next' }));
            }
        }

        function runNextStep() {
             if (currentProject && ['planning', 'coding', 'reviewing'].includes(currentProject.status.toLowerCase())) {
                 showToast('Triggering next step manually...', 'info');
                 ws.send(JSON.stringify({ type: 'project_next' }));
             } else {
                 showToast('No active project step to run.', 'error');
             }
        }

        function showNewProjectModal() {
            document.getElementById('project-modal').classList.add('active');
        }

        function closeModal() {
            document.getElementById('project-modal').classList.remove('active');
        }

        function createProject() {
            const name = document.getElementById('project-name').value;
            const desc = document.getElementById('project-desc').value;
            if (!name || !desc) return;
            ws.send(JSON.stringify({ type: 'project_create', name, prompt: desc }));
            closeModal();
        }

        function loadProject(name) {
            ws.send(JSON.stringify({ type: 'project_load', name }));
        }

        function handleKeyDown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        }

        function autoResize(el) {
            el.style.height = 'auto';
            el.style.height = Math.min(el.scrollHeight, 200) + 'px';
        }

        connect();
    </script>
</body>
</html>'''
