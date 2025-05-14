"""
title: GPT Researcher WebSocket Pipe
author: Edward
description: WebSocket-based pipe function for GPT Researcher
required_open_webui_version: 0.1.0
requirements: websockets
version: 0.1.0
licence: MIT
"""

import json
import asyncio
import websockets
from pydantic import BaseModel, Field
from typing import Union, Dict, Callable, Awaitable, Any, Generator, Iterator

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
        self.ws_lock = asyncio.Lock()

    def pipes(self):
        """Define the available pipe options."""
        return [
            {"id": "research_report", "name": "Basic Research Report (2-3 min)"},
            {"id": "detailed_report", "name": "Detailed Report (5 min)"},
            {"id": "deep", "name": "Deep Analysis Report (10 min)"},
        ]

    async def pipe(self, body: dict, __event_emitter__: Callable[[Any], Awaitable[None]]) -> Union[str, Generator, Iterator]:
        """Process the pipe request and return the research results."""
        # Extract parameters from body
        user_message = body.get("messages", [{}])[-1].get("content", "")
        report_type = body.get("model", self.valves.REPORT_TYPE)
        report_content = ""

        try:
            # Send initial status
            await __event_emitter__({"type": "status", "data": {"description": "연결 중...", "done": False}})

            # Connect to WebSocket
            try:
                self.websocket = await websockets.connect(
                    self.valves.SERVER_URL,
                    ping_interval=30,
                    ping_timeout=10
                )
            except Exception:
                await __event_emitter__({"type": "status", "data": {"description": "서버 연결 실패", "done": True}})
                return "GPT Researcher 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요."

            # Send the research request
            await __event_emitter__({"type": "status", "data": {"description": "연구 시작...", "done": False}})

            # Format the request
            request_data = {
                "task": user_message,
                "report_type": report_type,
                "report_source": self.valves.REPORT_SOURCE,
                "tone": self.valves.TONE,
                "source_urls": [],
                "document_urls": [],
                "query_domains": []
            }

            # Send the request
            await self.websocket.send(f"start {json.dumps(request_data)}")

            # Process messages until timeout or completion
            start_time = asyncio.get_event_loop().time()
            while True:
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > self.valves.TIMEOUT:
                    await __event_emitter__({"type": "status", "data": {"description": "시간 초과", "done": True}})
                    break

                # Wait for message with timeout
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)

                    # Handle ping/pong messages
                    if message == "pong":
                        continue

                    # Parse JSON data
                    data = json.loads(message)

                    # Process different message types
                    if isinstance(data, dict) and "type" in data:
                        if data["type"] == "report":
                            # For report content, accumulate it
                            content = data.get("output", "")
                            report_content += content
                            await __event_emitter__({"type": "chat:message:delta", "data": {"content": content}})
                        elif data["type"] == "logs":
                            # For logs, send as status updates
                            await __event_emitter__({"type": "status", "data": {"description": data.get("output", ""), "done": False}})
                        elif data["type"] == "path":
                            # When we receive path data, research is complete
                            await __event_emitter__({"type": "status", "data": {"description": "연구 완료", "done": True}})

                except asyncio.TimeoutError:
                    # No message received in timeout period, continue waiting
                    continue
                except websockets.exceptions.ConnectionClosed:
                    # Connection closed
                    await __event_emitter__({"type": "status", "data": {"description": "연결 종료", "done": True}})
                    break

            # Disconnect from WebSocket
            if self.websocket:
                await self.websocket.close()
                self.websocket = None

            # Return the final report content
            return report_content

        except Exception as e:
            # Handle any exceptions
            await __event_emitter__({"type": "status", "data": {"description": f"오류: {str(e)}", "done": True}})

            # Ensure WebSocket is closed
            if self.websocket:
                await self.websocket.close()
                self.websocket = None

            return f"오류가 발생했습니다: {str(e)}"
