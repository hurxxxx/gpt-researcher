"""
title: GPT Researcher Simple HTTP Pipe
author: Edward
description: Simple HTTP-based pipe function for GPT Researcher
required_open_webui_version: 0.1.0
requirements: aiohttp
version: 0.1.0
licence: MIT
"""

import json
import aiohttp
import asyncio
from pydantic import BaseModel, Field
from typing import Any

# We'll handle logs directly in the WebSocket handler

class Pipe:
    class Valves(BaseModel):
        SERVER_URL: str = Field(
            default="http://localhost:8000",
            description="HTTP URL for the GPT Researcher server (without trailing slash)"
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
        self.id = "gpt_researcher_simple"
        self.active_ws_task = None  # Track the active WebSocket task

    def pipes(self):
        """Define the available pipe options."""
        return [
            {"id": "research_report", "name": "Basic Research Report (2-3 min)"}
        ]

    async def _handle_websocket_logs(self, ws_url: str, request_data: dict, event_emitter):
        """Handle WebSocket connection to receive real-time logs."""
        session = None
        try:
            # Connect to WebSocket
            session = aiohttp.ClientSession()
            async with session.ws_connect(ws_url, timeout=30) as ws:
                print(f"WebSocket connection established to {ws_url}")

                # Send start command with research parameters
                start_command = {
                    "task": request_data["task"],
                    "report_type": request_data["report_type"],
                    "report_source": request_data["report_source"],
                    "tone": request_data["tone"],
                    "source_urls": [],
                    "agent": "Auto Agent",
                    "query_domains": []
                }

                await ws.send_str(f"start {json.dumps(start_command)}")
                print(f"Sent start command for task: {request_data['task'][:50]}...")

                # Listen for messages
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)

                            # Handle different message types
                            if data.get("type") == "logs" and "output" in data:
                                # Send log as status update
                                await event_emitter({
                                    "type": "status",
                                    "data": {
                                        "description": f"연구 진행 중: {data['output']}",
                                        "done": False,
                                    }
                                })
                            elif data.get("type") == "report" and "output" in data:
                                # Send report progress update
                                await event_emitter({
                                    "type": "status",
                                    "data": {
                                        "description": "리포트 작성 중...",
                                        "done": False,
                                    }
                                })
                            elif data.get("type") == "path" and "output" in data:
                                # Report is complete when path is received
                                print(f"Report files ready: {data['output']}")
                        except json.JSONDecodeError:
                            print(f"Invalid JSON received: {msg.data}")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"WebSocket error: {ws.exception()}")
                        break
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        print("WebSocket connection closed by server")
                        break
        except asyncio.CancelledError:
            # Task was cancelled, which is expected when HTTP response is received
            print("WebSocket task cancelled")
        except aiohttp.ClientConnectorError as e:
            print(f"Failed to connect to WebSocket server: {str(e)}")
            await event_emitter({
                "type": "status",
                "data": {
                    "description": f"WebSocket 서버 연결 실패: {str(e)}",
                    "done": False,
                }
            })
        except Exception as e:
            print(f"Error in WebSocket connection: {str(e)}")
            # Send error as status update
            await event_emitter({
                "type": "status",
                "data": {
                    "description": f"WebSocket 연결 오류: {str(e)}",
                    "done": False,
                }
            })
        finally:
            # Close the session if it was created
            if session:
                await session.close()
                print("WebSocket session closed")

    async def pipe(self, body: dict, __event_emitter__=None) -> Any:
        """Process the pipe request and return the research results."""
        # Extract parameters from body
        user_message = body.get("messages", [{}])[-1].get("content", "")
        report_type = body.get("model", self.valves.REPORT_TYPE)

        # Cancel any existing WebSocket task to prevent conflicts
        if self.active_ws_task and not self.active_ws_task.done():
            print("Cancelling existing WebSocket task")
            self.active_ws_task.cancel()
            try:
                await self.active_ws_task
            except asyncio.CancelledError:
                pass
            self.active_ws_task = None

        # Send status update before starting report generation
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": "리포트 생성을 시작합니다...",
                    "done": False,
                }
            })

        # We'll use WebSocket directly for real-time logs

        # ResearchRequest 모델에 맞게 요청 형식 지정
        request_data = {
            "task": user_message,  # 서버 모델에서는 'task'가 필수 필드
            "report_type": report_type,
            "report_source": self.valves.REPORT_SOURCE,
            "tone": self.valves.TONE,
            "headers": None,
            "repo_name": "default",
            "branch_name": "main",
            "generate_in_background": False  # 즉시 결과를 받기 위해 False로 설정
        }

        # Start a WebSocket connection for real-time logs
        ws_protocol = "wss" if self.valves.SERVER_URL.startswith("https") else "ws"
        ws_url = f"{ws_protocol}://{self.valves.SERVER_URL.replace('https://', '').replace('http://', '')}/ws"
        ws_task = None

        if __event_emitter__:
            # Create a task to handle WebSocket messages
            ws_task = asyncio.create_task(self._handle_websocket_logs(ws_url, request_data, __event_emitter__))
            # Store the task reference
            self.active_ws_task = ws_task

        # Send the HTTP request and get the response
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.valves.SERVER_URL}/report/",
                    json=request_data,
                    timeout=3600  # 60 minutes timeout
                ) as response:
                    # 응답 상태 코드와 상관없이 응답 내용 출력
                    response_text = await response.text()
                    print(f"Server response status: {response.status}")
                    print(f"Server response headers: {response.headers}")
                    print(f"Server response body: {response_text[:1000]}")

                    # Cancel the WebSocket task if it's still running
                    if ws_task and not ws_task.done():
                        ws_task.cancel()
                        try:
                            await asyncio.wait_for(ws_task, timeout=2.0)
                        except (asyncio.TimeoutError, asyncio.CancelledError):
                            pass

                    # Clear the active task reference
                    if self.active_ws_task == ws_task:
                        self.active_ws_task = None

                    if response.status != 200:
                        # Send error status update
                        if __event_emitter__:
                            await __event_emitter__({
                                "type": "status",
                                "data": {
                                    "description": f"서버 오류가 발생했습니다 ({response.status})",
                                    "done": True,
                                }
                            })
                        return f"서버 오류 ({response.status}): {response_text}"

                    try:
                        # 응답이 JSON인지 확인
                        try:
                            data = json.loads(response_text)

                            # Prepare the result
                            result = None
                            if "report" in data:
                                result = data["report"]
                            # Check for research_information
                            elif "research_information" in data:
                                result = data.get("report", str(data))
                            # Otherwise return whatever we got
                            elif "message" in data:
                                result = data["message"]
                            else:
                                result = str(data)

                            # Send status update after report generation is complete
                            if __event_emitter__:
                                await __event_emitter__({
                                    "type": "status",
                                    "data": {
                                        "description": "리포트 생성이 완료되었습니다.",
                                        "done": True,
                                    }
                                })

                            return result
                        except json.JSONDecodeError:
                            print("Response is not valid JSON")
                            # Send error status update
                            if __event_emitter__:
                                await __event_emitter__({
                                    "type": "status",
                                    "data": {
                                        "description": "응답 형식 오류가 발생했습니다",
                                        "done": True,
                                    }
                                })
                            return response_text
                    except Exception as e:
                        print(f"Error processing response: {str(e)}")
                        # Send error status update
                        if __event_emitter__:
                            await __event_emitter__({
                                "type": "status",
                                "data": {
                                    "description": f"응답 처리 중 오류가 발생했습니다: {str(e)}",
                                    "done": True,
                                }
                            })
                        return response_text
            except Exception as e:
                # Send error status update
                if __event_emitter__:
                    await __event_emitter__({
                        "type": "status",
                        "data": {
                            "description": f"요청 중 오류가 발생했습니다: {str(e)}",
                            "done": True,
                        }
                    })
                return f"오류가 발생했습니다: {str(e)}"
            finally:
                # Ensure WebSocket task is properly cleaned up
                if ws_task and not ws_task.done():
                    ws_task.cancel()
                    try:
                        await asyncio.wait_for(ws_task, timeout=2.0)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass

                # Clear the active task reference if it matches
                if self.active_ws_task == ws_task:
                    self.active_ws_task = None
