# GPT Researcher WebSocket Pipe Function

This pipe function allows you to connect OpenWebUI to a running GPT Researcher server using WebSockets. It enables you to send research requests to the GPT Researcher server and receive streaming results in real-time.

## Prerequisites

1. A running GPT Researcher server (typically on port 8000)
2. OpenWebUI installed and configured
3. The `websockets` Python package installed

## Installation

1. Copy the `websocket_pipe_function.py` file to your OpenWebUI's `oui` directory.
2. Install the required dependencies:
   ```bash
   pip install websockets
   ```

## Configuration

The pipe function can be configured through the following valves:

- **SERVER_URL**: The WebSocket URL for the GPT Researcher server (default: `ws://localhost:8000/ws`)
- **TIMEOUT**: Timeout in seconds for WebSocket connection (default: 300)
- **REPORT_TYPE**: Default report type (options: `research_report`, `detailed_report`, `deep`)
- **REPORT_SOURCE**: Source for research (options: `web`, `local`, `hybrid`)
- **TONE**: Tone of the report (options: `Objective`, `Formal`, `Analytical`, `Persuasive`, `Informative`, `Explanatory`, `Descriptive`, `Critical`, `Comparative`, `Speculative`, `Reflective`, `Narrative`, `Humorous`, `Optimistic`, `Pessimistic`, `Simple`, `Casual`)

## Usage

1. Start your GPT Researcher server:
   ```bash
   cd /path/to/gpt-researcher
   python main.py
   ```

2. Start OpenWebUI and select the "GPT Researcher WebSocket" model from the model selector.

3. Configure the valves as needed in the OpenWebUI settings.

4. Enter your research query and submit it.

5. The pipe function will connect to the GPT Researcher server, send your query, and stream the results back to OpenWebUI in real-time.

## How It Works

1. The pipe function establishes a WebSocket connection to the GPT Researcher server.
2. It sends a research request with your query and selected parameters.
3. It processes the streaming responses from the server and formats them for OpenWebUI.
4. It handles various message types (logs, report content, etc.) and provides status updates.
5. When the research is complete, it returns the final report content.

## Troubleshooting

- **Connection Issues**: Ensure the GPT Researcher server is running and accessible at the configured URL.
- **Timeout Errors**: If your research is taking longer than expected, increase the TIMEOUT value.
- **Missing Dependencies**: Make sure the `websockets` package is installed.

## Testing

You can test the pipe function using the provided `test_websocket_pipe.py` script:

```bash
python test_websocket_pipe.py
```

This script simulates how OpenWebUI would use the pipe function and prints the results to the console.

## License

MIT
