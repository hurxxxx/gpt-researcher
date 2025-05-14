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
from typing import List, Union, Dict, Generator, Iterator
from gpt_researcher import GPTResearcher
import time


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

    async def _conduct_research(self, query: str) -> Dict:
        try:
            researcher = GPTResearcher(query=query, report_type="research_report")
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
        model_id: str,
        messages: List[dict],
        body: dict,
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

        # chat:message:delta
        yield {
            "event": {
                "type": "chat:message:delta",
                "data": {
                    "content": "이거슨 델타",
                },
            }
        }

        # 연구 수행
        research_results = asyncio.run(self._conduct_research(user_message))

        # 결과 전달
        yield research_results["report"]

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
