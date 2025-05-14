"""
title: GPT Researcher WebSocket Streaming Pipe
author: Edward
description: WebSocket-based streaming pipe function for GPT Researcher
required_open_webui_version: 0.1.0
requirements: aiohttp
version: 0.1.1
licence: MIT
"""

import json
import aiohttp
from pydantic import BaseModel, Field
from typing import Any, Dict, Callable, Awaitable, Optional

class CustomLogsHandler:
    """A custom Logs handler class to handle WebSocket streaming data."""
    def __init__(self, event_emitter: Callable[[Any], Awaitable[None]]):
        self.logs = []  # Initialize logs to store data
        self.__event_emitter__ = event_emitter

    async def send_json(self, data: Dict[str, Any]) -> None:
        """Send JSON data and log it."""
        self.logs.append(data)  # Append data to logs

        # Send status update with log data
        if isinstance(data, dict):
            if "type" in data and "output" in data:
                # For logs and report data
                if data["type"] == "report":
                    content = data["output"]
                else:
                    content = data["output"] + "\n"

                await self.__event_emitter__({
                    "type": "chat:message:delta",
                    "data": {
                        "content": content,
                    }
                })

                # Also send status update with log content
                await self.__event_emitter__({
                    "type": "status",
                    "data": {
                        "description": content,
                        "log": content,
                        "done": False,
                    }
                })
            else:
                # For other data types
                await self.__event_emitter__({
                    "type": "status",
                    "data": {
                        "description": str(data),
                        "log": str(data),
                        "done": False,
                    }
                })


class Pipe:
    class Valves(BaseModel):
        SERVER_URL: str = Field(
            default="ws://localhost:8000/ws",
            description="WebSocket URL for the GPT Researcher server"
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
            description="Tone of the report"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.id = "gpt_researcher_websocket"

    def pipes(self):
        """Define the available pipe options."""
        return [
            {"id": "research_report", "name": "Basic Research Report (2-3 min)"},
            {"id": "detailed_report", "name": "Detailed Report (5 min)"},
            {"id": "deep", "name": "Deep Analysis Report (10 min)"}
        ]

    async def pipe(self, body: dict, __event_emitter__=None) -> Any:
        """Process the pipe request and return the research results using WebSocket streaming."""
        if __event_emitter__ is None:
            return "Event emitter is required for WebSocket streaming"

        # Extract parameters from body
        user_message = body.get("messages", [{}])[-1].get("content", "")
        report_type = body.get("model", self.valves.REPORT_TYPE)

        # Initialize the custom logs handler with the event emitter
        logs_handler = CustomLogsHandler(__event_emitter__)

        # Send initial status update
        await __event_emitter__({
            "type": "status",
            "data": {
                "description": "연구를 시작합니다...",
                "log": "연구를 시작합니다...",
                "done": False,
            }
        })

        # Prepare the request data
        request_data = {
            "task": user_message,
            "report_type": report_type,
            "report_source": self.valves.REPORT_SOURCE,
            "tone": self.valves.TONE,
            "agent": "researcher"  # Default agent
        }

        # Connect to the WebSocket server and stream the research process
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self.valves.SERVER_URL) as websocket:
                    # Send the start command with the request data
                    await websocket.send_str(f"start {json.dumps(request_data)}")

                    # Process WebSocket messages
                    final_report = ""

                    # Listen for WebSocket messages
                    async for msg in websocket:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                print(f"Received WebSocket data: {data}")

                                # Process different types of messages
                                if data.get("type") == "logs":
                                    # Forward log messages to the client
                                    await logs_handler.send_json(data)
                                elif data.get("type") == "report":
                                    # Store the report content
                                    final_report = data.get("output", "")
                                    await logs_handler.send_json(data)
                                elif data.get("type") == "path":
                                    # Research is complete
                                    await __event_emitter__({
                                        "type": "status",
                                        "data": {
                                            "description": "연구가 완료되었습니다.",
                                            "log": "연구가 완료되었습니다.",
                                            "done": True,
                                        }
                                    })
                                else:
                                    # Forward other message types
                                    await logs_handler.send_json(data)
                            except json.JSONDecodeError:
                                print(f"Received non-JSON message: {msg.data}")
                                if msg.data == "pong":
                                    # Heartbeat response, ignore
                                    continue
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"WebSocket error: {msg.data}")
                            await __event_emitter__({
                                "type": "status",
                                "data": {
                                    "description": f"WebSocket 오류: {msg.data}",
                                    "log": f"WebSocket 오류: {msg.data}",
                                    "done": True,
                                }
                            })
                            break
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            print("WebSocket connection closed")
                            break

                    # Return the final report
                    return final_report
        except Exception as e:
            error_message = f"연결 오류: {str(e)}"
            print(error_message)
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": error_message,
                    "log": error_message,
                    "done": True,
                }
            })
            return error_message
