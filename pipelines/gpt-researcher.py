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
from pydantic import BaseModel, Field
from typing import List, Union, Generator, Iterator
from gpt_researcher import GPTResearcher


class Pipeline:
    class Valves(BaseModel):
        OPENAI_API_KEY: str = Field(default="", description="OpenAI API Key")
        TAVILY_API_KEY: str = Field(default="", description="Tavily API Key")

    def __init__(self):
        self.id = "GPT-Researcher"
        self.name = "GPT-Researcher Pipeline"
        # Initialize valve parameters
        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )
        os.environ["OPENAI_API_KEY"] = self.valves.OPENAI_API_KEY
        os.environ["TAVILY_API_KEY"] = self.valves.TAVILY_API_KEY

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup: {__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is shutdown.
        print(f"on_shutdown: {__name__}")
        pass

    async def _conduct_research(self, query: str) -> tuple:
        researcher = GPTResearcher(query, "research_report")
        await researcher.conduct_research()
        report = await researcher.write_report()
        research_costs = researcher.get_costs()
        research_sources = researcher.get_research_sources()
        return report, research_costs, research_sources

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        # Get the last user message as the research query
        query = user_message

        # Run research asynchronously
        report, costs, sources = asyncio.run(self._conduct_research(query))

        # Format the response
        response = f"Research Report:\n\n{report}\n\nCosts: {costs}\n\nSources:\n"
        for source in sources:
            response += f"- {source.get('title', 'Unknown')}\n"

        # Yield the response line by line
        for line in response.split("\n"):
            yield line.encode("utf-8")
