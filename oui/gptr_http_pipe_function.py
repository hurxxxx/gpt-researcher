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
from enum import Enum
import aiohttp
from pydantic import BaseModel, Field
from typing import Any, Optional, Callable, Dict, Union, TypeVar
from open_webui.utils.chat import generate_chat_completion

# 상수 정의
DEFAULT_TIMEOUT = 600  # 10 minutes
T = TypeVar('T')

class ReportSource(str, Enum):
    WEB = "web"
    LOCAL = "local"
    HYBRID = "hybrid"

class ReportType(str, Enum):
    RESEARCH = "research_report"
    DETAILED = "detailed_report"
    DEEP = "deep"

class ReportTone(str, Enum):
    OBJECTIVE = "Objective"

class StatusMessage(BaseModel):
    description: str
    done: bool

class ResearchRequest(BaseModel):
    task: str
    report_type: str
    report_source: ReportSource
    tone: ReportTone
    headers: Optional[Dict[str, str]] = None
    repo_name: str = "default"
    branch_name: str = "main"
    generate_in_background: bool = False

class Pipe:
    class Valves(BaseModel):
        SERVER_URL: str = Field(
            default="http://localhost:8000",
            description="HTTP URL for the GPT Researcher server (without trailing slash)"
        )
        REPORT_TYPE: ReportType = Field(
            default=ReportType.RESEARCH,
            description="Default report type (research_report, detailed_report, deep)"
        )
        REPORT_SOURCE: ReportSource = Field(
            default=ReportSource.WEB,
            description="Source for research (web, local, hybrid)"
        )
        TONE: ReportTone = Field(
            default=ReportTone.OBJECTIVE,
            description="Tone of the report"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.id = "gpt_researcher_simple"

    def pipes(self) -> list[dict[str, str]]:
        """Define the available pipe options."""
        return [
            {"id": "research_report", "name": "Basic Research Report (2-3 min)"}
        ]

    async def _emit_status(
        self,
        emitter: Optional[Callable],
        description: str,
        done: bool
    ) -> None:
        """Helper function to emit status updates."""
        if emitter:
            await emitter({
                "type": "status",
                "data": StatusMessage(
                    description=description,
                    done=done
                ).dict()
            })

    async def _process_response(
        self,
        response_text: str
    ) -> Union[str, Dict[str, Any]]:
        """Process and validate the response from the server."""
        try:
            data = json.loads(response_text)
            
            if "report" in data:
                return data["report"]
            if "research_information" in data:
                return data.get("report", str(data))
            if "message" in data:
                return data["message"]
            
            return str(data)
        except json.JSONDecodeError:
            print("Response is not valid JSON")
            return response_text

    async def _make_request(
        self,
        request_data: ResearchRequest,
        emitter: Optional[Callable] = None
    ) -> str:
        """Make HTTP request to the research server."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.valves.SERVER_URL}/report/",
                    json=request_data.dict(),
                    timeout=DEFAULT_TIMEOUT
                ) as response:
                    response_text = await response.text()
                    print(f"Server response status: {response.status}")
                    
                    if response.status != 200:
                        await self._emit_status(
                            emitter,
                            f"서버 오류가 발생했습니다 ({response.status})",
                            True
                        )
                        return f"서버 오류 ({response.status}): {response_text}"

                    result = await self._process_response(response_text)
                    return str(result)

            except Exception as e:
                await self._emit_status(
                    emitter,
                    f"요청 중 오류가 발생했습니다: {str(e)}",
                    True
                )
                return f"오류가 발생했습니다: {str(e)}"

    async def pipe(self, body: dict, __event_emitter__: Optional[Callable] = None) -> Any:
        """Process the pipe request and return the research results."""
        user_message = body.get("messages", [{}])[-1].get("content", "")
        report_type = body.get("model", self.valves.REPORT_TYPE)

        await self._emit_status(
            __event_emitter__,
            "리포트 생성을 시작합니다...",
            False
        )

        request = ResearchRequest(
            task=user_message,
            report_type=report_type,
            report_source=self.valves.REPORT_SOURCE,
            tone=self.valves.TONE,
            headers=None,
            generate_in_background=False
        )

        result = await self._make_request(request, __event_emitter__)
        
        await self._emit_status(
            __event_emitter__,
            "리포트 생성이 완료되었습니다.",
            True
        )

        return result
