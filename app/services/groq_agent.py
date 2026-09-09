import json
import os
import time
from typing import Any, Callable

from groq import Groq

from app.rag.retriever import search_faq
from app.tools.escalation_tool import escalate_to_human
from app.tools.order_tool import get_order_status


class GroqAgent:
    """
    Agentic orchestration layer.

    The LLM decides whether it needs to call:
        - get_order_status
        - search_faq
        - escalate_to_human

    Includes:
        - Tool calling
        - Tool retry
        - Tool fallback
        - LLM retry
        - LLM fallback
        - Agent trace
        - Latency measurement
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        self.client = Groq(api_key=api_key)

        # Current Groq model.
        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b",
        )

        self.max_tool_retries = 2
        self.max_llm_retries = 2

        self.system_prompt = """
You are an AI customer support agent.

You have access to three tools:

1. get_order_status
   Use this when the customer asks about an order.

2. search_faq
   Use this when the customer asks a general support question.

3. escalate_to_human
   Use this when the customer explicitly asks for a human
   or when the issue cannot reasonably be solved with the
   available tools.

Rules:
- Do not invent order information.
- Use tools when appropriate.
- Keep answers concise and conversational.
- This system will eventually be connected to a voice bot,
  so avoid unnecessarily long responses.
"""

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_order_status",
                    "description": (
                        "Get the current status of a customer order."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": (
                                    "The customer's order ID."
                                ),
                            }
                        },
                        "required": ["order_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_faq",
                    "description": (
                        "Search the FAQ knowledge base for "
                        "customer support information."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": (
                                    "The customer's question."
                                ),
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "escalate_to_human",
                    "description": (
                        "Escalate the conversation to a human "
                        "support agent."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "description": (
                                    "Reason for escalation."
                                ),
                            }
                        },
                        "required": ["reason"],
                    },
                },
            },
        ]

        self.tool_functions: dict[
            str, Callable[..., Any]
        ] = {
            "get_order_status": get_order_status,
            "search_faq": search_faq,
            "escalate_to_human": escalate_to_human,
        }

    # ==========================================================
    # TOOL EXECUTION
    # ==========================================================

    def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """
        Execute a registered tool.
        """

        if tool_name not in self.tool_functions:
            raise ValueError(
                f"Unknown tool: {tool_name}"
            )

        tool_function = self.tool_functions[tool_name]

        return tool_function(**arguments)

    # ==========================================================
    # TOOL FALLBACK
    # ==========================================================

    def get_tool_fallback(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        error: str,
    ) -> dict[str, Any]:
        """
        Return a safe fallback response when a tool fails.
        """

        if tool_name == "get_order_status":
            return {
                "success": False,
                "fallback": True,
                "message": (
                    "I couldn't retrieve the order status "
                    "right now. Please try again or speak "
                    "with a human support agent."
                ),
                "error": error,
            }

        if tool_name == "search_faq":
            return {
                "success": False,
                "fallback": True,
                "message": (
                    "I couldn't access the support knowledge "
                    "base right now. Please try again or "
                    "speak with a human support agent."
                ),
                "error": error,
            }

        if tool_name == "escalate_to_human":
            return {
                "success": False,
                "fallback": True,
                "message": (
                    "The human-support escalation service "
                    "is temporarily unavailable."
                ),
                "error": error,
            }

        return {
            "success": False,
            "fallback": True,
            "message": (
                "The requested support operation is "
                "temporarily unavailable."
            ),
            "error": error,
        }

    # ==========================================================
    # TOOL RETRY
    # ==========================================================

    def execute_tool_with_retry(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        trace: list[dict[str, Any]],
    ) -> Any:
        """
        Execute a tool with retry and fallback.
        """

        last_error = ""

        for attempt in range(
            self.max_tool_retries + 1
        ):
            start_time = time.perf_counter()

            try:
                result = self.execute_tool(
                    tool_name,
                    arguments,
                )

                end_time = time.perf_counter()

                latency_ms = (
                    end_time - start_time
                ) * 1000

                trace.append(
                    {
                        "type": "tool",
                        "tool": tool_name,
                        "attempt": attempt + 1,
                        "status": "success",
                        "latency_ms": round(
                            latency_ms,
                            2,
                        ),
                    }
                )

                return result

            except Exception as exc:
                end_time = time.perf_counter()

                latency_ms = (
                    end_time - start_time
                ) * 1000

                last_error = str(exc)

                trace.append(
                    {
                        "type": "tool",
                        "tool": tool_name,
                        "attempt": attempt + 1,
                        "status": "error",
                        "error": last_error,
                        "latency_ms": round(
                            latency_ms,
                            2,
                        ),
                    }
                )

                # Retry if attempts remain.
                if attempt < self.max_tool_retries:
                    continue

        # All retries failed.
        fallback_result = self.get_tool_fallback(
            tool_name,
            arguments,
            last_error,
        )

        trace.append(
            {
                "type": "tool_fallback",
                "tool": tool_name,
                "status": "fallback",
            }
        )

        return fallback_result

    # ==========================================================
    # LLM CALL
    # ==========================================================

    def call_llm(
        self,
        messages: list[dict[str, Any]],
        trace: list[dict[str, Any]],
    ):
        """
        Call Groq with retry.
        """

        last_error = ""

        for attempt in range(
            self.max_llm_retries + 1
        ):
            start_time = time.perf_counter()

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0,
                )

                end_time = time.perf_counter()

                latency_ms = (
                    end_time - start_time
                ) * 1000

                trace.append(
                    {
                        "type": "llm",
                        "attempt": attempt + 1,
                        "status": "success",
                        "latency_ms": round(
                            latency_ms,
                            2,
                        ),
                    }
                )

                return response

            except Exception as exc:
                end_time = time.perf_counter()

                latency_ms = (
                    end_time - start_time
                ) * 1000

                last_error = str(exc)

                trace.append(
                    {
                        "type": "llm",
                        "attempt": attempt + 1,
                        "status": "error",
                        "error": last_error,
                        "latency_ms": round(
                            latency_ms,
                            2,
                        ),
                    }
                )

                if attempt < self.max_llm_retries:
                    continue

        raise RuntimeError(
            f"Groq LLM failed after retries: {last_error}"
        )

    # ==========================================================
    # MAIN AGENT
    # ==========================================================

    def run(self, user_message: str) -> dict[str, Any]:
        """
        Run the complete agentic workflow.
        """

        overall_start = time.perf_counter()

        trace: list[dict[str, Any]] = []

        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        # ------------------------------------------------------
        # FIRST LLM CALL
        # ------------------------------------------------------

        response = self.call_llm(
            messages,
            trace,
        )

        assistant_message = (
            response.choices[0].message
        )

        # ------------------------------------------------------
        # IMPORTANT FIX
        #
        # Explicitly type this as a generic dictionary.
        # This prevents Pylance from inferring:
        #
        # dict[str, str]
        #
        # and then complaining when tool_calls are added.
        # ------------------------------------------------------

        assistant_message_data: dict[str, Any] = {
            "role": "assistant",
            "content": (
                assistant_message.content
                or ""
            ),
        }

        # ------------------------------------------------------
        # TOOL CALLS
        # ------------------------------------------------------

        if assistant_message.tool_calls:

            tool_calls_data: list[
                dict[str, Any]
            ] = []

            for call in (
                assistant_message.tool_calls
            ):

                tool_calls_data.append(
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": (
                                call.function.name
                            ),
                            "arguments": (
                                call.function.arguments
                            ),
                        },
                    }
                )

            assistant_message_data[
                "tool_calls"
            ] = tool_calls_data

        messages.append(
            assistant_message_data
        )

        # ------------------------------------------------------
        # EXECUTE TOOLS
        # ------------------------------------------------------

        if assistant_message.tool_calls:

            for tool_call in (
                assistant_message.tool_calls
            ):

                tool_name = (
                    tool_call.function.name
                )

                raw_arguments = (
                    tool_call.function.arguments
                )

                try:
                    arguments = json.loads(
                        raw_arguments
                    )

                except json.JSONDecodeError:

                    arguments = {}

                    trace.append(
                        {
                            "type": "tool_arguments",
                            "tool": tool_name,
                            "status": "invalid_json",
                        }
                    )

                result = (
                    self.execute_tool_with_retry(
                        tool_name,
                        arguments,
                        trace,
                    )
                )

                # --------------------------------------------------
                # TOOL RESULT
                # --------------------------------------------------

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            result,
                            ensure_ascii=False,
                        ),
                    }
                )

            # --------------------------------------------------
            # FINAL LLM RESPONSE
            # --------------------------------------------------

            final_start = time.perf_counter()

            try:

                final_response = (
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0,
                    )
                )

                final_end = time.perf_counter()

                final_latency_ms = (
                    final_end - final_start
                ) * 1000

                trace.append(
                    {
                        "type": "llm_final",
                        "status": "success",
                        "latency_ms": round(
                            final_latency_ms,
                            2,
                        ),
                    }
                )

                final_message = (
                    final_response
                    .choices[0]
                    .message
                    .content
                    or ""
                )

            except Exception as exc:

                final_end = time.perf_counter()

                final_latency_ms = (
                    final_end - final_start
                ) * 1000

                trace.append(
                    {
                        "type": "llm_final",
                        "status": "error",
                        "error": str(exc),
                        "latency_ms": round(
                            final_latency_ms,
                            2,
                        ),
                    }
                )

                final_message = (
                    "I was able to process your request, "
                    "but I'm having trouble generating "
                    "the final response right now."
                )

        else:

            # --------------------------------------------------
            # NO TOOL REQUIRED
            # --------------------------------------------------

            final_message = (
                assistant_message.content
                or ""
            )

        # ------------------------------------------------------
        # TOTAL LATENCY
        # ------------------------------------------------------

        overall_end = time.perf_counter()

        total_latency_ms = (
            overall_end - overall_start
        ) * 1000

        # ------------------------------------------------------
        # RETURN
        # ------------------------------------------------------

        return {
            "response": final_message,
            "model": self.model,
            "total_latency_ms": round(
                total_latency_ms,
                2,
            ),
            "trace": trace,
        }