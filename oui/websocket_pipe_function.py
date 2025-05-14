"""
title: GPT Researcher WebSocket Pipe
author: Edward
description: WebSocket-based pipe function for GPT Researcher
required_open_webui_version: 0.1.0
requirements: websockets
version: 0.1.0
licence: MIT
"""

import os
import json
import asyncio
import websockets
from pydantic import BaseModel, Field
from typing import Union, Dict, Callable, Awaitable, Any, Optional, List, Generator, Iterator

class CustomWebSocketHandler:
    """A custom handler to process WebSocket messages from gpt-researcher server."""
    def __init__(self, event_emitter: Callable[[Any], Awaitable[None]]):
        self.event_emitter = event_emitter
        self.report_content = ""

    async def process_message(self, message: str) -> None:
        """Process a message received from the WebSocket."""
        try:
            # Handle ping/pong messages
            if message == "pong":
                return

            # Parse JSON data
            data = json.loads(message)

            # Process different message types
            if isinstance(data, dict):
                if "type" in data:
                    if data["type"] == "report":
                        # For report content, accumulate it
                        self.report_content += data.get("output", "")
                        await self.event_emitter({
                            "type": "chat:message:delta",
                            "data": {
                                "content": data.get("output", ""),
                            }
                        })
                    elif data["type"] == "logs":
                        # For logs, send as status updates
                        await self.event_emitter({
                            "type": "status",
                            "data": {
                                "description": data.get("output", ""),
                                "done": False,
                            }
                        })
                    elif data["type"] == "path":
                        # When we receive path data, research is complete
                        await self.event_emitter({
                            "type": "status",
                            "data": {
                                "description": "Research complete",
                                "done": True,
                            }
                        })
        except Exception as e:
            await self.event_emitter({
                "type": "status",
                "data": {
                    "description": f"Error processing message: {str(e)}",
                    "done": False,
                }
            })

class Pipe:
    class Valves(BaseModel):
        SERVER_URL: str = Field(
            default="ws://localhost:8000/ws",
            description="WebSocket URL for the GPT Researcher server"
        )
        TIMEOUT: int = Field(
            default=300,
            description="Timeout in seconds for WebSocket connection"
        )
        REPORT_TYPE: str = Field(
            default="research_report",
            description="Default report type (research_report, detailed_report, deep)"
        )
        REPORT_SOURCE: str = Field(
            default="web",
            description="Source for research (web, local, hybrid)"
        )
        TONE: str = Field(
            default="Objective",
            description="Tone of the report (Objective, Formal, Analytical, Persuasive, Informative, Explanatory, Descriptive, Critical, Comparative, Speculative, Reflective, Narrative, Humorous, Optimistic, Pessimistic, Simple, Casual)"
        )


    def __init__(self):
        self.valves = self.Valves()
        self.id = "gpt_researcher_websocket"
        self.websocket = None
        self.ws_lock = asyncio.Lock()  # Lock for WebSocket operations

    def pipes(self):
        """Define the available pipe options."""
        return [
            {"id": "research_report", "name": "Basic Research Report (2-3 min)"},
            {"id": "detailed_report", "name": "Detailed Report (5 min)"},
            {"id": "deep", "name": "Deep Analysis Report (10 min)"},
        ]

    async def connect_websocket(self):
        """Connect to the GPT Researcher WebSocket server."""
        try:
            self.websocket = await websockets.connect(
                self.valves.SERVER_URL,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5
            )
            return True
        except Exception:
            return False

    async def disconnect_websocket(self):
        """Disconnect from the WebSocket server."""
        if self.websocket:
            async with self.ws_lock:
                await self.websocket.close()
                self.websocket = None

    async def send_research_request(self, task: str, report_type: str):
        """Send a research request to the server."""
        if not self.websocket:
            success = await self.connect_websocket()
            if not success:
                raise Exception(f"Failed to connect to WebSocket server at {self.valves.SERVER_URL}")

        # Format the request according to gpt-researcher's expected format
        request_data = {
            "task": task,
            "report_type": report_type,
            "report_source": self.valves.REPORT_SOURCE,
            "tone": self.valves.TONE,
            "source_urls": [],
            "document_urls": [],
            "query_domains": []
        }

        # Send the request using the lock to ensure exclusive access
        async with self.ws_lock:
            await self.websocket.send(f"start {json.dumps(request_data)}")

    async def pipe(self, body: dict, __event_emitter__: Callable[[Any], Awaitable[None]]) -> Union[str, Generator, Iterator]:
        """Process the pipe request and return the research results."""
        # Extract parameters from body
        user_message = body.get("messages", [{}])[-1].get("content", "")
        report_type = body.get("model", self.valves.REPORT_TYPE)

        # Create a handler for WebSocket messages
        handler = CustomWebSocketHandler(__event_emitter__)

        try:
            # Send initial status
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": "Connecting to GPT Researcher server...",
                    "done": False,
                }
            })

            # Connect to WebSocket
            success = await self.connect_websocket()
            if not success:
                await __event_emitter__({
                    "type": "status",
                    "data": {
                        "description": f"Failed to connect to WebSocket server at {self.valves.SERVER_URL}",
                        "done": True,
                    }
                })
                return "Failed to connect to GPT Researcher server. Please check if the server is running."

            # Send the research request
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": "Starting research...",
                    "done": False,
                }
            })

            await self.send_research_request(user_message, report_type)

            # Process messages until timeout or completion
            start_time = asyncio.get_event_loop().time()
            while True:
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > self.valves.TIMEOUT:
                    await __event_emitter__({
                        "type": "status",
                        "data": {
                            "description": "Research timed out",
                            "done": True,
                        }
                    })
                    break

                # Wait for message with timeout
                try:
                    # Use the lock to ensure exclusive access to the WebSocket
                    async with self.ws_lock:
                        message = await asyncio.wait_for(
                            self.websocket.recv(),
                            timeout=5.0
                        )
                    await handler.process_message(message)
                except asyncio.TimeoutError:
                    # No message received in timeout period, continue waiting
                    continue
                except websockets.exceptions.ConnectionClosed:
                    # Connection closed
                    await __event_emitter__({
                        "type": "status",
                        "data": {
                            "description": "Connection to server closed",
                            "done": True,
                        }
                    })
                    break

            # Disconnect from WebSocket
            await self.disconnect_websocket()

            # Return the final report content
            return handler.report_content

        except Exception as e:
            # Handle any exceptions
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": f"Error: {str(e)}",
                    "done": True,
                }
            })

            # Ensure WebSocket is closed
            await self.disconnect_websocket()

            return f"An error occurred: {str(e)}"
