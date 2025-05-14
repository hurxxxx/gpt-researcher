"""
title: Langgraph stream integration with GPT Researcher
author: bartonzzx
author_url: https://github.com/bartonzzx
git_url:
description: Integrate GPT Researcher with open webui pipeline
required_open_webui_version: 0.4.3
requirements: gpt-researcher
version: 0.4.3
licence: MIT
"""

import os
import asyncio
import threading
import queue
from pydantic import BaseModel, Field
from typing import List, Union, Dict, Generator, Iterator, Any
from gpt_researcher import GPTResearcher
import time


class CustomWebSocketHandler:
    """Custom WebSocket handler to stream chat:message:delta events"""

    def __init__(self, message_queue=None):
        self.message_queue = message_queue

    async def send_json(self, data):
        """Handle the send_json method called by GPT Researcher"""
        # Only process data with type and output
        if isinstance(data, dict) and "type" in data and "output" in data:
            # Create message event
            message = {
                "event": {
                    "type": "chat:message:delta",
                    "data": {
                        "content": data["output"],
                    },
                }
            }

            # If message queue is provided, add message to queue
            if self.message_queue:
                self.message_queue.put(message)


class Pipeline:
    class Valves(BaseModel):
        OPENAI_API_KEY: str = Field(default="", description="OpenAI API Key")
        TAVILY_API_KEY: str = Field(default="", description="Tavily API Key")
        LANGUAGE: str = Field(default="korean", description="Report Language")

    def __init__(self):
        self.id = "gpt_researcher"
        self.name = "GPT 보고서"
        # Initialize valve parameters
        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )
        os.environ["OPENAI_API_KEY"] = self.valves.OPENAI_API_KEY
        os.environ["TAVILY_API_KEY"] = self.valves.TAVILY_API_KEY
        os.environ["LANGUAGE"] = self.valves.LANGUAGE

    async def _conduct_research(self, query: str, websocket=None) -> Dict:
        try:
            researcher = GPTResearcher(
                query=query, report_type="research_report", websocket=websocket
            )
            await researcher.conduct_research()
            report = await researcher.write_report()

            # Get additional information
            # research_context = researcher.get_research_context()
            # research_costs = researcher.get_costs()
            # research_images = researcher.get_research_images()
            # research_sources = researcher.get_research_sources()

            return {
                "report": report,
                "context": None,
                "costs": None,
                "images": None,
                "sources": None,
            }
        except Exception as e:
            print(f"Research Error: {str(e)}")
            return {
                "report": f"연구 중 오류가 발생했습니다: {str(e)}",
                "context": None,
                "costs": None,
                "images": None,
                "sources": None,
            }

    def pipe(
        self,
        user_message: str,
        model_id: str = None,  # 파라미터는 유지하되 사용하지 않음
        messages: List[dict] = None,  # 파라미터는 유지하되 사용하지 않음
        body: dict = None,  # 파라미터는 유지하되 사용하지 않음
    ) -> Union[str, Generator, Iterator]:
        # 시작 이벤트 전달
        yield {
            "event": {
                "type": "status",
                "data": {
                    "description": "연구를 시작합니다...",
                    "done": False,
                },
            }
        }

        # 메시지 큐 생성
        message_queue = queue.Queue()

        # 연구 수행을 위한 스레드 생성
        def run_research():
            nonlocal research_results
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            websocket_handler = CustomWebSocketHandler(message_queue=message_queue)
            research_results = loop.run_until_complete(
                self._conduct_research(user_message, websocket=websocket_handler)
            )
            # 연구 완료 표시
            message_queue.put(None)

        # 연구 결과 변수 초기화
        research_results = None

        # 스레드 시작
        research_thread = threading.Thread(target=run_research)
        research_thread.start()

        # 메시지 큐에서 메시지를 가져와 yield
        while True:
            try:
                message = message_queue.get(timeout=0.1)
                if message is None:
                    # 연구 완료
                    break
                yield message
            except queue.Empty:
                # 큐가 비어있으면 계속 대기
                continue

        # 스레드 종료 대기
        research_thread.join()

        # 결과 전달
        yield research_results["report"] if research_results else "연구 결과를 가져오지 못했습니다."

        # 완료 이벤트 전달
        yield {
            "event": {
                "type": "status",
                "data": {
                    "description": "연구가 완료되었습니다.",
                    "done": True,
                },
            }
        }
