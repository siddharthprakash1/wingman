"""
Reproduction script for project creation failure.
"""

import asyncio
import json
import logging
import sys

import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reproduce_project_creation():
    uri = "ws://127.0.0.1:18789/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to gateway")

            # 1. Initialize
            init_msg = {
                "type": "init",
                "session_id": "test_session"
            }
            await websocket.send(json.dumps(init_msg))
            response = await websocket.recv()
            logger.info(f"Init response: {response}")

            # 2. Create Project
            create_msg = {
                "type": "project_create",
                "name": "TestProject",
                "prompt": "Create a simple Python script that prints 'Hello World'"
            }
            logger.info(f"Sending create project message: {create_msg}")
            await websocket.send(json.dumps(create_msg))

            # 3. Listen for updates
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                logger.info(f"Received: {data}")
                
                if data.get("type") == "error":
                    logger.error(f"Error received: {data.get('content')}")
                    break
                    
                if data.get("type") == "project_update":
                    msg = data.get("message", "")
                    if "Plan created" in msg:
                        logger.info("Plan created successfully!")
                        break

    except Exception as e:
        logger.error(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(reproduce_project_creation())
