# 기업 분석 보고서
from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Any, Optional, TypedDict, List, Dict, Union
from gpt_researcher import GPTResearcher
from open_webui.routers.retrieval import process_web_search, SearchForm
from open_webui.utils.middleware import chat_web_search_handler
from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.misc import get_last_user_message
from open_webui.models.users import Users, UserModel

import json
import re
import asyncio
import os


class Pipeline:
    class Valves(BaseModel):
        status: bool = Field(default=True)
        OPENAI_API_KEY: str = Field(default="")
        TAVILY_API_KEY: str = Field(default="")
        LANGUAGE: str = Field(default="korean")

    async def emit_status(
        self,
        __event_emitter__: Callable[[dict], Awaitable[None]],
        level: str,
        message: str,
        done: bool,
    ):
        if self.valves.status:
            await __event_emitter__(
                {
                    "type": level,
                    "data": {
                        "description": message,
                        "done": done,
                    },
                }
            )

    def __init__(self):
        self.valves = self.Valves(
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""),
            TAVILY_API_KEY=os.getenv("TAVILY_API_KEY", ""),
            LANGUAGE=os.getenv("LANGUAGE", "korean"),
        )

    async def get_report(self, query: str, report_type: str):
        # 환경 변수 설정
        os.environ["OPENAI_API_KEY"] = self.valves.OPENAI_API_KEY
        os.environ["TAVILY_API_KEY"] = self.valves.TAVILY_API_KEY
        os.environ["LANGUAGE"] = self.valves.LANGUAGE

        researcher = GPTResearcher(query=query, report_type=report_type)
        research_result = await researcher.conduct_research()
        report = await researcher.write_report()

        # Get additional information
        research_context = researcher.get_research_context()
        research_costs = researcher.get_costs()
        research_images = researcher.get_research_images()
        research_sources = researcher.get_research_sources()

        return (
            report,
            research_context,
            research_costs,
            research_images,
            research_sources,
        )

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __request__: Any,
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
    ) -> dict:
        try:
            user = Users.get_user_by_id(__user__["id"]) if __user__ else None

            messages = body["messages"]
            user_message = get_last_user_message(messages)

            report_type = "research_report"
            report, context, costs, images, sources = await self.get_report(
                user_message, report_type
            )

        

            await self.emit_status(
                __event_emitter__,
                level="status",
                message="최종 기업 분석 보고서 요청 프롬프트 생성 완료",
                done=True,
            )

            return report

        except Exception as e:
            print(f"오류 발생: {str(e)}")
            print(f"오류 상세 정보:")
            print(f"오류 유형: {type(e).__name__}")
            print(
                f"오류 발생 위치: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}"
            )
            print(f"오류 상세 메시지: {str(e)}")

            import traceback

            print("스택 트레이스:")
            print("".join(traceback.format_tb(e.__traceback__)))

        return body
