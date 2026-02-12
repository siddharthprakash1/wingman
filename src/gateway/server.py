"""
Gateway Server — FastAPI + WebSocket control plane.

The central hub that routes messages between channels and the agent.
Serves the WebChat UI and provides REST/WebSocket APIs.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.agent.loop import AgentSession
from src.config.settings import get_settings, load_settings
from src.gateway.session import SessionManager
from src.gateway.router import MessageRouter

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(
        title="OpenClaw Mine Gateway",
        description="Personal AI Assistant Control Plane",
        version="0.1.0",
    )

    settings = load_settings()
    session_manager = SessionManager()
    router = MessageRouter(session_manager)

    # -----------------------------------------------------------------------
    # REST Endpoints
    # -----------------------------------------------------------------------

    @app.get("/", response_class=HTMLResponse)
    async def index():
        """Serve the WebChat UI."""
        from src.channels.webchat import get_webchat_html
        return get_webchat_html()

    @app.get("/api/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "model": settings.agents.defaults.model,
        }

    @app.get("/api/config")
    async def get_config():
        """Get current configuration (sanitized)."""
        config = settings.model_dump()
        # Mask API keys
        for provider in config.get("providers", {}).values():
            if isinstance(provider, dict) and "api_key" in provider:
                key = provider["api_key"]
                if key and len(key) > 8:
                    provider["api_key"] = key[:4] + "****" + key[-4:]
                elif key:
                    provider["api_key"] = "****"
        return config

    @app.get("/api/sessions")
    async def list_sessions():
        """List all sessions."""
        return {"sessions": session_manager.list_sessions()}

    @app.get("/api/tools")
    async def list_tools():
        """List available tools."""
        from src.tools.registry import create_default_registry
        registry = create_default_registry()
        return {"tools": registry.list_tools()}

    # -----------------------------------------------------------------------
    # WebSocket Endpoint
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # WebSocket Endpoint
    # -----------------------------------------------------------------------

    # Initialize Project Manager
    from src.agents.coding.orchestrator import ProjectManager
    project_manager = ProjectManager()

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time chat."""
        await websocket.accept()
        logger.info("WebSocket client connected")

        # Create or resume session
        session_id = None
        agent_session = None

        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                msg_type = message.get("type", "message")

                if msg_type == "init":
                    # Initialize session
                    session_id = message.get("session_id")
                    agent_session = session_manager.get_or_create(session_id)
                    
                    # Send init data + current project state if any
                    response_data = {
                        "type": "session",
                        "session_id": agent_session.session_id,
                        "model": agent_session.settings.agents.defaults.model,
                    }
                    if project_manager.current_project:
                         response_data["project"] = project_manager.current_project.to_dict()
                    
                    await websocket.send_json(response_data)

                elif msg_type == "message":
                    if agent_session is None:
                        agent_session = session_manager.get_or_create()

                    user_text = message.get("content", "").strip()
                    if not user_text:
                        continue

                    # Send "thinking" indicator
                    await websocket.send_json({"type": "thinking", "status": True})

                    try:
                        # Process through agent loop
                        response = await agent_session.process_message(
                            user_text, channel="webchat"
                        )
                        await websocket.send_json({
                            "type": "response",
                            "content": response,
                            "session_id": agent_session.session_id,
                        })
                    except Exception as e:
                        logger.error(f"Agent error: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "content": f"Agent error: {e}",
                        })
                    finally:
                        await websocket.send_json({"type": "thinking", "status": False})
                
                # --- Project Management Handlers ---
                
                elif msg_type == "project_create":
                    name = message.get("name")
                    prompt = message.get("prompt")
                    try:
                        state = project_manager.create_project(name, prompt)
                        await websocket.send_json({
                            "type": "project_update",
                            "project": state.to_dict()
                        })
                        # Auto-start planning
                        status_msg = await project_manager.run_next_step()
                        await websocket.send_json({
                            "type": "project_update",
                            "project": project_manager.current_project.to_dict(),
                            "message": status_msg
                        })
                    except Exception as e:
                        await websocket.send_json({"type": "error", "content":str(e)})

                elif msg_type == "project_load":
                    name = message.get("name")
                    state = project_manager.load_project(name)
                    if state:
                        await websocket.send_json({
                            "type": "project_update",
                            "project": state.to_dict()
                        })
                    else:
                         await websocket.send_json({"type": "error", "content": "Project not found"})

                elif msg_type == "project_list":
                    projects = project_manager.list_projects()
                    await websocket.send_json({
                        "type": "project_list",
                        "projects": projects
                    })

                elif msg_type == "project_next":
                    # Run next step
                    try:
                        await websocket.send_json({"type": "thinking", "status": True})
                        status_msg = await project_manager.run_next_step()
                        await websocket.send_json({
                            "type": "project_update",
                            "project": project_manager.current_project.to_dict(),
                            "message": status_msg
                        })
                    except Exception as e:
                        logger.error(f"Project step error: {e}")
                        await websocket.send_json({"type": "error", "content": str(e)})
                    finally:
                        await websocket.send_json({"type": "thinking", "status": False})

                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
            if agent_session:
                agent_session.save_session()
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    return app


async def start_gateway(host: str = "127.0.0.1", port: int = 18789):
    """Start the gateway server."""
    import uvicorn

    app = create_app()

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        ws_max_size=16 * 1024 * 1024,  # 16MB WebSocket messages
    )
    server = uvicorn.Server(config)

    # Start channel listeners in background
    settings = load_settings()
    tasks: list[asyncio.Task] = []

    if settings.channels.telegram.enabled:
        try:
            from src.channels.telegram import start_telegram_bot
            tasks.append(asyncio.create_task(
                start_telegram_bot(settings),
            ))
            logger.info("Telegram bot starting...")
        except Exception as e:
            logger.warning(f"Failed to start Telegram: {e}")

    if settings.channels.discord.enabled:
        try:
            from src.channels.discord import start_discord_bot
            tasks.append(asyncio.create_task(
                start_discord_bot(settings),
            ))
            logger.info("Discord bot starting...")
        except Exception as e:
            logger.warning(f"Failed to start Discord: {e}")

    # Run the server
    await server.serve()

    # Cleanup
    for task in tasks:
        task.cancel()
