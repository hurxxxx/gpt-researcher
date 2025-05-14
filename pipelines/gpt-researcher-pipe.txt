requirements: "gpt-researcher"
import os
import asyncio
import traceback
from pydantic import BaseModel, Field
from datetime import datetime

try:
    from gpt_researcher import GPTResearcher  # Import the installed package

    # The ResearchProgress class is used internally by gpt-researcher,
    # we don't need to explicitly import/define it here,
    # unless we want type hinting for the callback parameter.
except ImportError:
    # Fallback or error message if the package is not found
    print("ERROR: Could not import the package 'gpt-researcher'.")
    print(
        "Ensure it is installed in the container: pip install gpt-researcher"
    )
    GPTResearcher = None  # Set to None to allow later errors


class Pipe:
    """
    A customized Open WebUI Pipe function for gpt-researcher
    with detailed configuration via Valves, status updates via Event Emitter,
    and support for "Deep Research" mode.
    """

    class Valves(BaseModel):
        # --- LLM / API Configuration ---
        OPENAI_BASE_URL: str = Field(
            default="http://xyz:4000/v1",
            description="Base URL for the (local) OpenAI-compatible endpoint.",
        )
        OPENAI_API_KEY: str = Field(
            default="sk-xyz",
            description="API key for the LLM endpoint (possibly a dummy value).",
        )
        FAST_LLM_MODEL: str = Field(
            default="openai:xyz",
            description="Model name for fast tasks (e.g., subtopic generation).",
        )
        SMART_LLM_MODEL: str = Field(
            default="openai:xyz",  # For Deep Research, a reasoning model is recommended
            description="Model name for main research and writing tasks.",
        )
        STRATEGIC_LLM_MODEL: str = Field(
            default="openai:xyz",  # Important for Deep Research
            description="Model name for strategic planning tasks (used for Deep Research).",
        )
        EMBEDDING_MODEL: str = Field(
            default="openai:xyz",
            description="Model name for text embeddings.",
        )

        # --- Retriever Configuration ---
        RETRIEVER: str = Field(
            default="searx",
            description="Retriever to use ('searx', 'tavily', 'duckduckgo', etc.).",
        )
        SEARX_INSTANCE_URL: str = Field(
            default="http://xyz",
            description="URL of the SearxNG instance (only relevant if RETRIEVER='searx').",
        )

        # --- Research Parameters ---
        REPORT_TYPE: str = Field(
            default="deep",  # Default set to 'deep'
            description="Type of report ('deep', 'research_report', 'resource_report', 'outline_report', 'custom_report').",
        )
        LANGUAGE: str = Field(
            default="english", description="Language for the research and report."
        )
        REPORT_FORMAT: str = Field(
            default="markdown",  # Markdown is often good for WebUI
            description="Format of the report (e.g., 'markdown', 'APA', 'MLA', 'Harvard style').",
        )
        TOTAL_WORDS: int = Field(
            default=3000,
            description="Approximate target word count for the report (Recommendation for 'deep': >=3000).",
        )
        MAX_ITERATIONS: int = Field(  # May be less relevant for 'deep'
            default=3,
            description="Maximum number of research iterations per subtopic (less relevant for 'deep').",
        )
        MAX_SUBTOPICS: int = Field(  # May be less relevant for 'deep'
            default=3,
            description="Maximum number of subtopics (less relevant for 'deep').",
        )
        TEMPERATURE: float = Field(
            default=0.55,
            description="Temperature for LLM generation (creativity).",
        )

        # --- Deep Research Parameters (NEW) ---
        DEEP_RESEARCH_BREADTH: int = Field(
            default=2,
            description="Number of parallel research paths per level for 'deep' mode.",
        )
        DEEP_RESEARCH_DEPTH: int = Field(
            default=2,
            description="Number of levels for deep research in 'deep' mode.",
        )
        DEEP_RESEARCH_CONCURRENCY: int = Field(
            default=4,
            description="Maximum number of simultaneous research operations for 'deep' mode.",
        )

        # --- Token / Length Limits ---
        FAST_TOKEN_LIMIT: int = Field(default=4000)
        SMART_TOKEN_LIMIT: int = Field(default=4000)
        STRATEGIC_TOKEN_LIMIT: int = Field(default=4000)  # Important for Deep Research
        BROWSE_CHUNK_MAX_LENGTH: int = Field(default=8192)
        SUMMARY_TOKEN_LIMIT: int = Field(default=2000)

        VERBOSE: bool = Field(
            default=False,
            description="Enable/disable verbose logging.",
        )

    def __init__(self):
        """Initializes the Pipe and its Valves."""
        self.valves = self.Valves()
        if GPTResearcher is None:
            print("WARNING: GPTResearcher could not be imported on startup.")

    async def pipe(self, body: dict, __user__: dict = None, __event_emitter__=None):
        """
        The main function of the Pipe, which processes the request and sends status updates,
        now with support for Deep Research and detailed progress.
        """
        print(f"GPT Researcher Custom Pipe called with Query and configuration.")

        # Ensure the emitter is available
        if not __event_emitter__:
            print(
                "WARNING: __event_emitter__ was not provided. Status updates are disabled."
            )

            async def dummy_emitter(*args, **kwargs):
                pass

            _emitter = dummy_emitter
        else:
            _emitter = __event_emitter__

        if GPTResearcher is None:
            await _emitter(
                {
                    "type": "status",
                    "data": {
                        "description": "Error: GPT-Researcher not initialized.",
                        "done": True,
                        "hidden": False,
                    },
                }
            )
            return "Error: The 'gpt-researcher' package is not correctly installed or importable. Please check server logs."

        original_env = os.environ.copy()

        # --- Define the on_progress Callback ---
        async def deep_research_progress_callback(progress_data):
            """Sends detailed progress updates during Deep Research."""
            # progress_data is an object with attributes like current_depth, total_depth, etc.
            try:
                # Try to safely get attributes
                cd = getattr(progress_data, "current_depth", "?")
                td = getattr(progress_data, "total_depth", "?")
                cb = getattr(progress_data, "current_breadth", "?")
                tb = getattr(progress_data, "total_breadth", "?")
                cq = getattr(progress_data, "current_query", "...")
                comp_q = getattr(progress_data, "completed_queries", "?")
                total_q = getattr(progress_data, "total_queries", "?")

                # Format message
                message = (
                    f"Deep Research: {comp_q}/{total_q} completed. "
                    f"(Depth {cd}/{td}, Breadth {cb}/{tb}) "
                    f"Current: '{cq[:30]}...'"
                )

                if self.valves.VERBOSE:
                    print(f"PROGRESS UPDATE: {message}")  # Also output to server log

                await _emitter(
                    {
                        "type": "status",
                        "data": {
                            "description": message,
                            "done": False,
                            "hidden": False,
                        },
                    }
                )
            except Exception as e:
                print(f"Error in Progress Callback: {e}")
                # Do not re-raise the error to avoid disturbing the main process

        try:
            # --- Set Environment Variables (incl. Deep Research Params) ---
            print("Setting environment variables for gpt-researcher...")
            os.environ["OPENAI_BASE_URL"] = self.valves.OPENAI_BASE_URL
            os.environ["OPENAI_API_KEY"] = self.valves.OPENAI_API_KEY
            os.environ["FAST_LLM"] = self.valves.FAST_LLM_MODEL
            os.environ["SMART_LLM"] = self.valves.SMART_LLM_MODEL
            os.environ["STRATEGIC_LLM"] = (
                self.valves.STRATEGIC_LLM_MODEL
            )  # Important for Deep
            os.environ["EMBEDDING"] = self.valves.EMBEDDING_MODEL
            os.environ["RETRIEVER"] = self.valves.RETRIEVER
            if self.valves.RETRIEVER == "searx" and self.valves.SEARX_INSTANCE_URL:
                os.environ["SEARX_URL"] = self.valves.SEARX_INSTANCE_URL

            os.environ["TEMPERATURE"] = str(self.valves.TEMPERATURE)
            os.environ["LANGUAGE"] = self.valves.LANGUAGE
            os.environ["FAST_TOKEN_LIMIT"] = str(self.valves.FAST_TOKEN_LIMIT)
            os.environ["SMART_TOKEN_LIMIT"] = str(self.valves.SMART_TOKEN_LIMIT)
            os.environ["STRATEGIC_TOKEN_LIMIT"] = str(
                self.valves.STRATEGIC_TOKEN_LIMIT
            )  # Important for Deep
            os.environ["SUMMARY_TOKEN_LIMIT"] = str(self.valves.SUMMARY_TOKEN_LIMIT)
            os.environ["TOTAL_WORDS"] = str(
                self.valves.TOTAL_WORDS
            )  # Also applies to Deep

            # Set Deep Research environment variables
            os.environ["DEEP_RESEARCH_BREADTH"] = str(self.valves.DEEP_RESEARCH_BREADTH)
            os.environ["DEEP_RESEARCH_DEPTH"] = str(self.valves.DEEP_RESEARCH_DEPTH)
            os.environ["DEEP_RESEARCH_CONCURRENCY"] = str(
                self.valves.DEEP_RESEARCH_CONCURRENCY
            )

            # --- Extract Query ---
            query = body.get("messages", [{}])[-1].get("content", None)
            if not query:
                await _emitter(
                    {
                        "type": "status",
                        "data": {
                            "description": "Error: No query found.",
                            "done": True,
                            "hidden": False,
                        },
                    }
                )
                return "Error: Could not find a query in the request."

            print(f"Starting GPT Researcher for Query: '{query}'")
            report_mode = self.valves.REPORT_TYPE
            print(f"Report Type: {report_mode}, Format: {self.valves.REPORT_FORMAT}")
            if report_mode == "deep":
                print(
                    f"Deep Research Params: Depth={self.valves.DEEP_RESEARCH_DEPTH}, Breadth={self.valves.DEEP_RESEARCH_BREADTH}, Concurrency={self.valves.DEEP_RESEARCH_CONCURRENCY}"
                )

            # --- Status: Initialization ---
            initial_status_msg = (
                f"Initializing research for '{query[:40]}...' ({report_mode})"
            )
            if report_mode == "deep":
                initial_status_msg = (
                    f"Initializing Deep Research for '{query[:40]}...'"
                )

            await _emitter(
                {
                    "type": "status",
                    "data": {
                        "description": initial_status_msg,
                        "done": False,
                        "hidden": False,
                    },
                }
            )

            # --- Initialize GPTResearcher ---
            researcher = GPTResearcher(
                query=query,
                report_type=report_mode,  # Use the value from Valves
                report_format=self.valves.REPORT_FORMAT,
                max_subtopics=self.valves.MAX_SUBTOPICS,  # Less relevant for 'deep'
                verbose=self.valves.VERBOSE,
                # max_iterations, total_words etc. are usually controlled via Env Vars or Config
            )

            # --- Status: Research Running ---
            if report_mode == "deep":
                await _emitter(
                    {
                        "type": "status",
                        "data": {
                            "description": "Conducting Deep Research (may take > 5 minutes)...",
                            "done": False,
                            "hidden": False,
                        },
                    }
                )
                print("Conducting Deep Research...")
                # Pass the callback to conduct_research
                await researcher.conduct_research(
                    on_progress=deep_research_progress_callback
                )
            else:
                # Standard Research (as before)
                await _emitter(
                    {
                        "type": "status",
                        "data": {
                            "description": "Conducting Standard Research...",
                            "done": False,
                            "hidden": False,
                        },
                    }
                )
                print("Conducting Standard Research...")
                await researcher.conduct_research()  # Without callback

            # --- Status: Writing Report ---
            print("Writing report...")
            await _emitter(
                {
                    "type": "status",
                    "data": {
                        "description": "Writing the final report...",
                        "done": False,
                        "hidden": False,
                    },
                }
            )
            report = await researcher.write_report()
            images = researcher.get_research_images()
            sources = researcher.get_research_sources()

            # --- Status: Completed ---
            final_status_msg = f"{report_mode.capitalize()} Research completed."
            await _emitter(
                {
                    "type": "status",
                    "data": {
                        "description": final_status_msg,
                        "done": True,
                        "hidden": False,
                    },
                }
            )

            # --- Format Result ---
            response = report
            response += f"\n\n**Sources:**\n"
            if sources:
                for i, source in enumerate(sources):
                    url = (
                        source.get("url", str(source))
                        if isinstance(source, dict)
                        else str(source)
                    )
                    response += f"{i+1}. {url}\n"
            else:
                response += "No specific sources found.\n"

            print(f"GPT Researcher Custom Pipe ({report_mode}) completed.")
            return response

        except Exception as e:
            print(f"Error in GPT Researcher Custom Pipe: {e}")
            traceback.print_exc()
            # --- Status: Error ---
            error_msg = f"Error during {self.valves.REPORT_TYPE} Research: {str(e)}"
            await _emitter(
                {
                    "type": "status",
                    "data": {"description": error_msg, "done": True, "hidden": False},
                }
            )
            return f"An error occurred during research: {str(e)}. Check the server logs for details."