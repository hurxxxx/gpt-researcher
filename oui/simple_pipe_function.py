from pydantic import BaseModel, Field
import asyncio
import os
from typing import Union, Dict, Callable, Awaitable, Any, Optional, TypedDict, List
from gpt_researcher import GPTResearcher

class CustomLogsHandler:
    """A custom Logs handler class to handle JSON data."""
    def __init__(self, event_emitter: Callable[[Any], Awaitable[None]]):
        self.logs = []  # Initialize logs to store data
        self.__event_emitter__ = event_emitter

    async def send_json(self, data: Dict[str, Any]) -> None:
        """Send JSON data and log it."""
        self.logs.append(data)  # Append data to logs
        
        # Format message based on data type
        if isinstance(data, dict) and "type" in data and "output" in data:
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

class Pipe:
    class Valves(BaseModel):
        OPENAI_API_KEY: str = Field(
            default="",
            description="OpenAI API Key",
        )
        TAVILY_API_KEY: str = Field(
            default="",
            description="Tavily API Key",
        )
        LANGUAGE: str = Field(
            default="korean",
            description="Language",
        )
        REPORT_TYPE: str = Field(
            default="research_report",
            description="Report Type",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.id = "gpt_researcher"

    def pipes(self):
        return [
            {"id": "research_report", "name": "Basic Research Report (2-3 min)"},
            {"id": "detailed_report", "name": "Detailed Report (5 min)"},
            {"id": "deep", "name": "Deep Analysis Report (10 min)"},
        ]

    async def get_report(self, query: str, report_type: str, event_emitter: Callable[[Any], Awaitable[None]]) -> str:
        # Set environment variables for GPT Researcher
        os.environ["OPENAI_API_KEY"] = self.valves.OPENAI_API_KEY
        os.environ["TAVILY_API_KEY"] = self.valves.TAVILY_API_KEY
        os.environ["LANGUAGE"] = self.valves.LANGUAGE

        # Initialize researcher with query
        custom_logs_handler = CustomLogsHandler(event_emitter)
        researcher = GPTResearcher(query, report_type, custom_logs_handler)

        # Conduct research and generate report
        await researcher.conduct_research()
        report = await researcher.write_report()

        return report

    async def pipe(self, body: dict, __event_emitter__: Callable[[Any], Awaitable[None]]) -> Union[str, Dict]:
        # Extract parameters from body
        user_message = body.get("messages", [{}])[-1].get("content", "")
        report_type = body.get("model", self.valves.REPORT_TYPE)

        await __event_emitter__({
            "type": "status",
            "data": {
                "description": "시작",
                "done": True,
            },
        })

        report = await self.get_report(user_message, report_type, __event_emitter__)
        return report
        
        
        

