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
from pydantic import BaseModel, Field
from typing import Any

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

    def pipes(self):
        """Define the available pipe options."""
        return [
            {"id": "research_report", "name": "Basic Research Report (2-3 min)"}
        ]

    async def pipe(self, body: dict, __event_emitter__=None) -> Any:
        """Process the pipe request and return the research results."""
        # Extract parameters from body
        user_message = body.get("messages", [{}])[-1].get("content", "")
        report_type = body.get("model", self.valves.REPORT_TYPE)

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

        # Send the HTTP request and get the response
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.valves.SERVER_URL}/report/",
                    json=request_data,
                    timeout=600  # 10 minutes timeout
                ) as response:
                    # 응답 상태 코드와 상관없이 응답 내용 출력
                    response_text = await response.text()
                    print(f"Server response status: {response.status}")
                    print(f"Server response headers: {response.headers}")
                    print(f"Server response body: {response_text[:1000]}")

                    if response.status != 200:
                        return f"서버 오류 ({response.status}): {response_text}"

                    try:
                        # 응답이 JSON인지 확인
                        try:
                            data = json.loads(response_text)

                            # Return the report if available
                            if "report" in data:
                                return data["report"]
                            # Check for research_information
                            elif "research_information" in data:
                                return data.get("report", str(data))
                            # Otherwise return whatever we got
                            elif "message" in data:
                                return data["message"]
                            else:
                                return str(data)
                        except json.JSONDecodeError:
                            print("Response is not valid JSON")
                            return response_text
                    except Exception as e:
                        print(f"Error processing response: {str(e)}")
                        return response_text
            except Exception as e:
                return f"오류가 발생했습니다: {str(e)}"
