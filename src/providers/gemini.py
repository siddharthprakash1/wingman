"""
Google Gemini LLM provider.

Uses the google-genai SDK to call Gemini 2.5 Flash (free tier)
with native function calling support.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator

from src.providers.base import LLMProvider, LLMResponse, Message, ToolCall, ToolDefinition

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini provider using the google-genai SDK."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", api_base: str | None = None):
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        self._client = None

    def _get_client(self):
        """Lazy-init the Gemini client."""
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        """
        Convert our Message format to Gemini's content format.
        Returns (system_instruction, contents).
        """
        system_instruction = None
        contents: list[dict[str, Any]] = []

        for msg in messages:
            if msg.role == "system":
                # Gemini uses system_instruction separately
                system_instruction = msg.content
            elif msg.role == "user":
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg.content}],
                })
            elif msg.role == "assistant":
                parts: list[dict[str, Any]] = []
                if msg.content:
                    parts.append({"text": msg.content})
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        parts.append({
                            "function_call": {
                                "name": tc.name,
                                "args": tc.arguments,
                            }
                        })
                if parts:
                    contents.append({"role": "model", "parts": parts})
            elif msg.role == "tool":
                contents.append({
                    "role": "user",
                    "parts": [
                        {
                            "function_response": {
                                "name": msg.name or "unknown",
                                "response": {"result": msg.content},
                            }
                        }
                    ],
                })

        return system_instruction, contents

    def _convert_tools(self, tools: list[ToolDefinition]) -> list[dict[str, Any]] | None:
        """Convert tool definitions to Gemini function declarations."""
        if not tools:
            return None
        declarations = []
        for tool in tools:
            decl = tool.to_gemini_format()
            # Clean up parameters for Gemini compatibility
            params = decl.get("parameters", {})
            if params:
                # Gemini doesn't support 'additionalProperties' at top level
                params.pop("additionalProperties", None)
            declarations.append(decl)
        return [{"function_declarations": declarations}]

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        stream: bool = False,
    ) -> LLMResponse:
        """Send a chat request to Gemini."""
        client = self._get_client()
        system_instruction, contents = self._convert_messages(messages)
        gemini_tools = self._convert_tools(tools) if tools else None

        config: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        try:
            # Run the synchronous genai call in a thread
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.model if self.model.startswith("models/") else f"models/{self.model}",
                contents=contents,
                config={
                    "system_instruction": system_instruction,
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    "tools": gemini_tools,
                },
            )

            # Parse the response
            result = LLMResponse()

            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "text") and part.text:
                        result.content += part.text
                    elif hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        # Parse args — may be a dict or a proto map
                        args = {}
                        if hasattr(fc, "args") and fc.args:
                            if isinstance(fc.args, dict):
                                args = fc.args
                            else:
                                # Proto MapComposite → convert to dict
                                try:
                                    args = dict(fc.args)
                                except Exception:
                                    args = json.loads(str(fc.args))

                        result.tool_calls.append(ToolCall(
                            id=f"call_{fc.name}_{len(result.tool_calls)}",
                            name=fc.name,
                            arguments=args,
                        ))

            if result.tool_calls:
                result.finish_reason = "tool_calls"

            # Usage info if available
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                um = response.usage_metadata
                result.usage = {
                    "prompt_tokens": getattr(um, "prompt_token_count", 0),
                    "completion_tokens": getattr(um, "candidates_token_count", 0),
                    "total_tokens": getattr(um, "total_token_count", 0),
                }

            return result

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> AsyncIterator[str]:
        """Stream a chat completion from Gemini."""
        client = self._get_client()
        system_instruction, contents = self._convert_messages(messages)
        gemini_tools = self._convert_tools(tools) if tools else None

        try:
            response_stream = await asyncio.to_thread(
                client.models.generate_content_stream,
                model=self.model if self.model.startswith("models/") else f"models/{self.model}",
                contents=contents,
                config={
                    "system_instruction": system_instruction,
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    "tools": gemini_tools,
                },
            )

            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Gemini is configured and reachable."""
        if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY":
            return False
        try:
            client = self._get_client()
            # Try a minimal call
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.model if self.model.startswith("models/") else f"models/{self.model}",
                contents=[{"role": "user", "parts": [{"text": "ping"}]}],
                config={"max_output_tokens": 5},
            )
            return response is not None
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False

    def get_model_info(self) -> dict[str, Any]:
        """Return Gemini model metadata."""
        return {
            "provider": "gemini",
            "model": self.model,
            "context_window": 1_048_576,  # 1M tokens for Gemini 2.5
            "supports_function_calling": True,
            "supports_streaming": True,
            "free_tier": True,
        }
