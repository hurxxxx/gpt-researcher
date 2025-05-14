#!/usr/bin/env python3
"""
Test script for GPT Researcher report generation
This script sends a request to localhost:8000 to generate a report with the prompt "미국 뉴스" (American news)
and checks for any errors.
"""

import asyncio
import json
import aiohttp
import sys

# Configuration
SERVER_URL = "http://localhost:8000"
PROMPT = "미국 뉴스"  # American news
REPORT_TYPE = "research_report"  # Basic research report
REPORT_SOURCE = "web"  # Web search
TONE = "Objective"  # Objective tone

async def handle_websocket_logs(ws_url, request_data):
    """Handle WebSocket connection to receive real-time logs."""
    print(f"Connecting to WebSocket at {ws_url}...")
    try:
        # Connect to WebSocket
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                print("WebSocket connection established")
                
                # Send start command with research parameters
                start_command = {
                    "task": request_data["task"],
                    "report_type": request_data["report_type"],
                    "report_source": request_data["report_source"],
                    "tone": request_data["tone"],
                    "source_urls": [],
                    "agent": "Auto Agent",
                    "query_domains": []
                }

                await ws.send_str(f"start {json.dumps(start_command)}")
                print(f"Sent start command: {start_command}")

                # Listen for messages
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                            
                            # Handle different message types
                            if data.get("type") == "logs" and "output" in data:
                                print(f"LOG: {data['output']}")
                            elif data.get("type") == "report" and "output" in data:
                                print(f"REPORT PROGRESS: {data['output'][:100]}...")
                            elif data.get("type") == "path" and "output" in data:
                                print(f"REPORT FILES: {data['output']}")
                            else:
                                print(f"OTHER MESSAGE: {data}")
                        except json.JSONDecodeError:
                            print(f"Invalid JSON received: {msg.data}")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"WebSocket error: {ws.exception()}")
                        break
    except asyncio.CancelledError:
        print("WebSocket task cancelled")
    except Exception as e:
        print(f"Error in WebSocket connection: {str(e)}")
        raise

async def send_report_request():
    """Send HTTP request to generate a report."""
    # Prepare request data
    request_data = {
        "task": PROMPT,
        "report_type": REPORT_TYPE,
        "report_source": REPORT_SOURCE,
        "tone": TONE,
        "headers": None,
        "repo_name": "default",
        "branch_name": "main",
        "generate_in_background": False  # Get immediate results
    }
    
    # Start a WebSocket connection for real-time logs
    ws_protocol = "ws"  # Use ws for http, wss for https
    ws_url = f"{ws_protocol}://{SERVER_URL.replace('http://', '')}/ws"
    
    # Create a task to handle WebSocket messages
    ws_task = asyncio.create_task(handle_websocket_logs(ws_url, request_data))
    
    try:
        # Send the HTTP request and get the response
        print(f"Sending HTTP request to {SERVER_URL}/report/...")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{SERVER_URL}/report/",
                    json=request_data,
                    timeout=3600  # 60 minutes timeout
                ) as response:
                    # Print response status and headers
                    print(f"Server response status: {response.status}")
                    print(f"Server response headers: {response.headers}")
                    
                    # Get response text
                    response_text = await response.text()
                    print(f"Server response preview: {response_text[:500]}...")
                    
                    # Cancel the WebSocket task if it's still running
                    if not ws_task.done():
                        ws_task.cancel()
                    
                    if response.status != 200:
                        print(f"Server error ({response.status}): {response_text}")
                        return None
                    
                    try:
                        # Check if response is JSON
                        data = json.loads(response_text)
                        
                        # Extract report content
                        if "report" in data:
                            print("\n--- REPORT CONTENT PREVIEW ---")
                            print(data["report"][:500] + "...")
                            print("--- END OF PREVIEW ---\n")
                            return data["report"]
                        elif "research_information" in data:
                            print("\n--- RESEARCH INFORMATION ---")
                            print(json.dumps(data["research_information"], indent=2))
                            print("--- END OF RESEARCH INFORMATION ---\n")
                            return data.get("report", str(data))
                        elif "message" in data:
                            print(f"Server message: {data['message']}")
                            return data["message"]
                        else:
                            print(f"Unexpected response format: {data}")
                            return str(data)
                    except json.JSONDecodeError:
                        print("Response is not valid JSON")
                        return response_text
            except aiohttp.ClientError as e:
                print(f"HTTP request error: {str(e)}")
                return None
    except Exception as e:
        print(f"Error sending report request: {str(e)}")
        return None
    finally:
        # Make sure WebSocket task is cancelled
        if not ws_task.done():
            ws_task.cancel()
            try:
                await ws_task
            except asyncio.CancelledError:
                pass

async def main():
    """Main function to run the test."""
    print(f"Testing report generation with prompt: '{PROMPT}'")
    report = await send_report_request()
    
    if report:
        print("\nReport generation completed successfully!")
    else:
        print("\nReport generation failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
