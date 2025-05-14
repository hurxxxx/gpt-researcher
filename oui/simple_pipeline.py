from pydantic import BaseModel, Field

class Pipe:
    class Valves(BaseModel):
        MODEL_ID: str = Field(default="")

    def __init__(self):
        self.valves = self.Valves()

    def pipes(self):
        return [
            {"id": "research_report", "name": "기본 리서치 보고서 (2~3분)"},
            {"id": "detailed_report", "name": "상세 보고서 (5분)"},
            {"id": "deep", "name": "심층 분석 보고서 (10분)"},
        ]

    def pipe(self, body: dict):
        # Logic goes here
        print(self.valves, body)  # Prints the configuration options and the input body
        model = body.get("model", "")
        return f"{model}: Hello, World!"