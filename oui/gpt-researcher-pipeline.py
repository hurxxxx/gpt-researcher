"""
title: GPT 보고서
author: hurxxxx
git_url:
description: GPT 보고서
required_open_webui_version: 0.1.0
requirements: gpt-researcher
version: 0.1.0
licence: MIT
"""

import os
import asyncio
import threading
import queue
from pydantic import BaseModel, Field
from typing import List, Union, Dict, Generator, Iterator, Optional
from gpt_researcher import GPTResearcher


class CustomWebSocketHandler:

    def __init__(self, message_queue: Optional[queue.Queue] = None):
        self.message_queue = message_queue

    async def send_json(self, data: Dict) -> None:

        # Only process data with type and output fields
        if isinstance(data, dict) and "type" in data and "output" in data:
            # Format as chat:message:delta event

            # data["type"] == "logs"
            # data["type"] == "report"
            # data["type"] == "images"
            # data["type"] == "path"

            if data["type"] == "report":
                content = data["output"]
            else:
                content = data["output"] + "\n"

            message = {
                "event": {
                    "type": "chat:message:delta",
                    "data": {
                        "content": content,
                    },
                }
            }

            # Add to queue if available
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

        # Initialize valve parameters from environment variables
        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )

        # Set environment variables for GPT Researcher
        os.environ["OPENAI_API_KEY"] = self.valves.OPENAI_API_KEY
        os.environ["TAVILY_API_KEY"] = self.valves.TAVILY_API_KEY
        os.environ["LANGUAGE"] = self.valves.LANGUAGE

    async def _conduct_research(self, query: str, websocket=None) -> Dict:

        try:
            # Initialize researcher with query and websocket for streaming
            # research_report, deep, multi_agents, detailed_report
            researcher = GPTResearcher(
                query=query, report_type="research_report", websocket=websocket
            )

            # Conduct research and generate report
            await researcher.conduct_research()
            report = await researcher.write_report()

            # Return research results
            return {"report": report}
        except Exception as e:
            # Handle errors gracefully
            print(f"Research Error: {str(e)}")
            return {"report": f"연구 중 오류가 발생했습니다: {str(e)}"}

    def pipe(
        self,
        user_message: str,
        model_id: str = None,  # Required by interface but not used
        messages: List[dict] = None,  # Required by interface but not used
        body: dict = None,  # Required by interface but not used
    ) -> Union[str, Generator, Iterator]:

        # Send initial status event
        yield {
            "event": {
                "type": "status",
                "data": {
                    "description": "연구를 시작합니다...",
                    "done": False,
                },
            }
        }

        # Create message queue for real-time communication
        message_queue = queue.Queue()

        # Initialize research results
        research_results = None

        # Define research thread function
        def run_research():
            """Run research in a separate thread with its own event loop."""
            nonlocal research_results
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Create websocket handler that will send messages to our queue
            websocket_handler = CustomWebSocketHandler(message_queue=message_queue)

            # Run the research
            research_results = loop.run_until_complete(
                self._conduct_research(user_message, websocket=websocket_handler)
            )

            # Signal that research is complete
            message_queue.put(None)

        # Start research in separate thread
        research_thread = threading.Thread(target=run_research)
        research_thread.start()

        # Stream messages in real-time
        while True:
            try:
                # Get message from queue with timeout
                message = message_queue.get(timeout=0.1)

                # Check if research is complete
                if message is None:
                    break

                # Stream message to client
                yield message
            except queue.Empty:
                # Continue waiting if queue is empty
                continue

        # Wait for research thread to complete
        research_thread.join()

        # Send final report
        yield (
            research_results["report"]
            if research_results
            else "연구 결과를 가져오지 못했습니다."
        )

        # Send completion status event
        yield {
            "event": {
                "type": "status",
                "data": {
                    "description": "연구가 완료되었습니다.",
                    "done": True,
                },
            }
        }
