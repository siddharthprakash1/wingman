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

    class ConnectionManager:
        def __init__(self):
            # List of active connections
            self.active_connections: list[WebSocket] = []

        async def connect(self, websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            logger.info(f"Client connected. Active connections: {len(self.active_connections)}")

        def disconnect(self, websocket: WebSocket):
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}")

        async def broadcast(self, message: dict):
            """Send a message to all connected clients."""
            # Iterate backwards to safely remove closed connections if needed
            for connection in self.active_connections[:]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send to client, removing: {e}")
                    self.disconnect(connection)

    connection_manager = ConnectionManager()

    # Helper function for running project steps in background (defined outside loop)
    async def _run_bg_step(manager, is_new=False):
        """Helper to run project step in background and notify frontend."""
        try:
            manager.is_busy = True
            # Notify start (Broadcast)
            await connection_manager.broadcast({"type": "thinking", "status": True})
            
            # Run step
            status_msg = await manager.run_next_step()
            
            manager.is_busy = False
            
            # Notify completion (Broadcast)
            if manager.current_project:
                await connection_manager.broadcast({
                    "type": "project_update",
                    "project": manager.current_project.to_dict(),
                    "message": status_msg
                })
        except Exception as e:
            logger.error(f"Background step error: {e}")
            manager.is_busy = False
            await connection_manager.broadcast({"type": "error", "content": str(e)})
        finally:
            manager.is_busy = False
            await connection_manager.broadcast({"type": "thinking", "status": False})

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time chat."""
        await connection_manager.connect(websocket)

        # Create or resume session
        session_id = None
        agent_session = None

        try:
            # Send initial "is busy" state if agent is running
            if project_manager.is_busy:
                 await websocket.send_json({"type": "thinking", "status": True})

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

                    # Send "thinking" indicator (Broadcast so all tabs see it)
                    await connection_manager.broadcast({"type": "thinking", "status": True})

                    try:
                        # Inject Project Context if available
                        if project_manager.current_project:
                            proj = project_manager.current_project
                            context_str = (
                                f"[Current Project Context]\n"
                                f"Name: {proj.name}\n"
                                f"Phase: {proj.status.value}\n"
                                f"Workspace: {proj.workspace_path}\n"
                            )
                            # Add current step info if planning is done
                            if proj.plan and 0 <= proj.current_step_index < len(proj.plan):
                                step = proj.plan[proj.current_step_index]
                                context_str += f"Current Step: {step.title} ({step.status.value})\n"
                            
                            user_text = f"{context_str}\nUser Query: {user_text}"

                        # Process through agent loop
                        response = await agent_session.process_message(
                            user_text, channel="webchat"
                        )
                        await connection_manager.broadcast({
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
                        await connection_manager.broadcast({"type": "thinking", "status": False})
                
                # --- Project Management Handlers ---

                if msg_type == "project_create":
                    name = message.get("name")
                    prompt = message.get("prompt")
                    try:
                        state = project_manager.create_project(name, prompt)
                        await connection_manager.broadcast({
                            "type": "project_update",
                            "project": state.to_dict()
                        })
                        # Auto-start planning in background
                        asyncio.create_task(_run_bg_step(project_manager, is_new=True))
                        
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

                elif msg_type == "project_delete":
                    name = message.get("name")
                    
                    if project_manager.is_busy:
                         await websocket.send_json({
                             "type": "error", 
                             "content": "Cannot delete project while agent is running!"
                         })
                         continue

                    try:
                        project_manager.delete_project(name)
                        # Broadcast updated list
                        projects = project_manager.list_projects()
                        await connection_manager.broadcast({
                            "type": "project_list",
                            "projects": projects
                        })
                    except Exception as e:
                        await websocket.send_json({"type": "error", "content": str(e)})

                elif msg_type == "project_list":
                    projects = project_manager.list_projects()
                    await websocket.send_json({
                        "type": "project_list",
                        "projects": projects
                    })

                elif msg_type == "project_next":
                    if project_manager.is_busy:
                         # Ignore if already running
                         continue
                         
                    # Run next step in BACKGROUND
                    asyncio.create_task(_run_bg_step(project_manager))

                elif msg_type == "file_upload":
                    # Handle file upload for document ingestion with progress
                    filename = message.get("filename", "unknown")
                    content_b64 = message.get("content", "")
                    
                    # Validate file extension
                    ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.md', '.html', '.htm', '.json', '.csv'}
                    file_ext = Path(filename).suffix.lower()
                    if file_ext not in ALLOWED_EXTENSIONS:
                        await websocket.send_json({
                            "type": "error",
                            "content": f"Unsupported file type: {file_ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
                        })
                        continue
                    
                    async def process_file_with_progress():
                        try:
                            import base64
                            import tempfile
                            from pathlib import Path
                            
                            # Step 1: Uploading
                            await websocket.send_json({
                                "type": "file_processing",
                                "filename": filename,
                                "step": "Decoding",
                            })
                            
                            # Decode base64 content
                            try:
                                file_content = base64.b64decode(content_b64)
                            except Exception as e:
                                await websocket.send_json({
                                    "type": "error",
                                    "content": f"Invalid file content: {e}",
                                })
                                return
                            
                            # Check file size (max 50MB)
                            MAX_UPLOAD_SIZE = 50 * 1024 * 1024
                            if len(file_content) > MAX_UPLOAD_SIZE:
                                await websocket.send_json({
                                    "type": "error",
                                    "content": f"File too large: {len(file_content) / (1024*1024):.1f}MB. Max: 50MB",
                                })
                                return
                            
                            # Save to temp file
                            suffix = Path(filename).suffix
                            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                                f.write(file_content)
                                temp_path = f.name
                            
                            # Step 2: Loading document
                            await websocket.send_json({
                                "type": "file_processing",
                                "filename": filename,
                                "step": "Reading document",
                            })
                            
                            from src.ingestion.processor import DocumentProcessor
                            from src.retrieval.vector_store import get_vector_store
                            
                            vector_store = get_vector_store()
                            processor = DocumentProcessor(vector_store=vector_store)
                            
                            # Step 3: Chunking
                            await websocket.send_json({
                                "type": "file_processing",
                                "filename": filename,
                                "step": "Chunking text",
                            })
                            
                            # Step 4: Generating embeddings
                            await websocket.send_json({
                                "type": "file_processing",
                                "filename": filename,
                                "step": "Generating embeddings",
                            })
                            
                            result = processor.process_file(
                                file_path=temp_path,
                                collection_name="documents",
                                extra_metadata={"original_filename": filename},
                            )
                            
                            # Clean up temp file
                            Path(temp_path).unlink(missing_ok=True)
                            
                            if result.success:
                                await websocket.send_json({
                                    "type": "file_uploaded",
                                    "filename": filename,
                                    "chunks": result.num_chunks,
                                    "characters": result.total_chars,
                                })
                            else:
                                await websocket.send_json({
                                    "type": "error",
                                    "content": f"Failed to process {filename}: {result.error}",
                                })
                                
                        except Exception as e:
                            logger.error(f"File upload error: {e}")
                            await websocket.send_json({
                                "type": "error",
                                "content": f"File upload failed: {e}",
                            })
                    
                    # Run file processing
                    await process_file_with_progress()

                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

        except WebSocketDisconnect:
            connection_manager.disconnect(websocket)
            if agent_session:
                agent_session.save_session()
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            # Try to send error to client before disconnecting
            try:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Server error: {str(e)[:200]}",
                })
            except Exception:
                pass  # Client already disconnected
            connection_manager.disconnect(websocket)

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
