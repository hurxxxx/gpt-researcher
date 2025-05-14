#!/usr/bin/env python3
"""
Test script for the GPT Researcher Simple HTTP Pipe function.
This script simulates how OpenWebUI would use the pipe function.
"""

import asyncio
import sys
import json
import aiohttp
from websocket_pipe_function import Pipe

async def test_direct_api():
    """Test the API directly without using the pipe function."""
    print("Testing direct API call...")

    # Get query from command line or use default
    query = sys.argv[1] if len(sys.argv) > 1 else "What are the latest developments in renewable energy?"
    report_type = sys.argv[2] if len(sys.argv) > 2 else "research_report"

    # Create request data
    request_data = {
        "task": query,
        "report_type": report_type,
        "report_source": "web",
        "tone": "Objective",
        "headers": None,
        "repo_name": "default",
        "branch_name": "main",
        "generate_in_background": False
    }

    # Send HTTP request
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "http://localhost:8000/report/",
                json=request_data,
                timeout=600
            ) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {response.headers}")
                text = await response.text()
                print(f"Response: {text[:1000]}")

                if response.status == 200:
                    try:
                        data = json.loads(text)
                        print("\nParsed JSON response:")
                        print(json.dumps(data, indent=2)[:1000])
                    except json.JSONDecodeError:
                        print("Response is not valid JSON")
        except Exception as e:
            print(f"Error: {str(e)}")

async def test_pipe():
    """Test using the pipe function."""
    print("Testing pipe function...")

    # Create a pipe instance
    pipe = Pipe()

    # Configure the pipe (optional)
    pipe.valves.SERVER_URL = "http://localhost:8000"  # Change this to your server URL

    # Get query from command line or use default
    query = sys.argv[1] if len(sys.argv) > 1 else "What are the latest developments in renewable energy?"
    report_type = sys.argv[2] if len(sys.argv) > 2 else "research_report"

    print(f"Query: {query}")
    print(f"Report type: {report_type}")

    # Create a test request body
    body = {
        "messages": [
            {"role": "user", "content": query}
        ],
        "model": report_type  # "research_report", "detailed_report", or "deep"
    }

    # Call the pipe function
    print("Starting research...")
    try:
        result = await pipe.pipe(body)

        # Print the result
        print("\nFinal result:")
        print(result[:500] + "..." if len(result) > 500 else result)
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function to run tests."""
    # First test direct API
    await test_direct_api()

    print("\n" + "-"*50 + "\n")

    # Then test pipe function
    await test_pipe()

if __name__ == "__main__":
    asyncio.run(main())
