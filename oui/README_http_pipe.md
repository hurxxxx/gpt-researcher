# GPT Researcher Simple HTTP Pipe Function

이 파이프 함수는 OpenWebUI를 GPT Researcher 서버에 HTTP 요청을 통해 연결합니다. 매우 간단한 구현으로 연구 요청을 보내고 결과를 받아옵니다.

## 필수 조건

1. 실행 중인 GPT Researcher 서버 (일반적으로 8000 포트)
2. OpenWebUI 설치 및 구성
3. `aiohttp` Python 패키지 설치

## 설치

1. `websocket_pipe_function.py` 파일을 OpenWebUI의 `oui` 디렉토리에 복사합니다 (파일 이름은 그대로지만 HTTP를 사용합니다).
2. 필요한 의존성 설치:
   ```bash
   pip install aiohttp pydantic
   ```

## 구성

파이프 함수에는 다음과 같은 구성 매개변수(valves)가 있습니다:

- `SERVER_URL`: GPT Researcher 서버의 기본 URL (기본값: "http://localhost:8000")
- `REPORT_TYPE`: 기본 보고서 유형 (기본값: "research_report")
- `REPORT_SOURCE`: 연구 소스 (기본값: "web")
- `TONE`: 보고서 톤 (기본값: "Objective")

## 사용법

1. GPT Researcher 서버 시작:
   ```bash
   cd /path/to/gpt-researcher
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. OpenWebUI를 시작하고 모델 선택기에서 "GPT Researcher Simple" 모델을 선택합니다.

3. 필요에 따라 OpenWebUI 설정에서 valves를 구성합니다.

4. 연구 쿼리를 입력하고 제출합니다.

5. 파이프 함수는 GPT Researcher 서버에 연결하여 쿼리를 보내고 결과를 받아옵니다.

## 작동 방식

1. 파이프 함수는 GPT Researcher 서버에 HTTP 연결을 설정합니다.
2. `/report/` 엔드포인트에 쿼리와 선택한 매개변수로 연구 요청을 보냅니다.
3. 서버로부터 응답을 받아 처리합니다.
4. 연구가 완료되면 최종 보고서 내용을 반환합니다.

## 오류 처리

파이프 함수는 다음과 같은 오류 상황을 처리합니다:

- GPT Researcher 서버 연결 오류
- 서버 응답 오류
- 일반적인 예외 처리

## 문제 해결

- **연결 문제**: GPT Researcher 서버가 실행 중이고 구성된 URL에서 접근 가능한지 확인하세요.
- **누락된 종속성**: `aiohttp` 및 `pydantic` 패키지가 설치되어 있는지 확인하세요.

## 라이센스

MIT
