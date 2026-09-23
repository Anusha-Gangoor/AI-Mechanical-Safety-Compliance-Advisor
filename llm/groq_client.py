"""
Groq API client for the AI Mechanical Safety Compliance Advisor.
Provides a clean, reusable interface to the Groq LLM API.
Model: openai/gpt-oss-120b
"""

import os
import json
from typing import Optional, List, Dict, Any

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


MODEL = "openai/gpt-oss-120b"


class GroqClientError(Exception):
    """Raised when the Groq client encounters a fatal error."""
    pass


class GroqClient:
    """
    Reusable Groq API client wrapper.

    Usage:
        client = GroqClient()
        response = client.chat("Your system prompt", "Your user message")
    """

    def __init__(self, api_key: Optional[str] = None, model: str = MODEL):
        self.model = model
        self._api_key = api_key or os.environ.get("GROQ_API_KEY", "")

        if not GROQ_AVAILABLE:
            raise GroqClientError(
                "The 'groq' package is not installed. Run: pip install groq"
            )

        if not self._api_key:
            raise GroqClientError(
                "GROQ_API_KEY environment variable is not set. "
                "Please add it to your .env file or environment."
            )

        self._client = Groq(api_key=self._api_key)

    @classmethod
    def is_configured(cls) -> bool:
        """Check whether the Groq API key is available without instantiating."""
        return bool(os.environ.get("GROQ_API_KEY", "").strip()) and GROQ_AVAILABLE

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> str:
        """
        Send a chat completion request to Groq.

        Args:
            system_prompt: The system-level instructions for the LLM.
            user_message: The user-level input message.
            temperature: Sampling temperature (lower = more deterministic).
            max_tokens: Maximum tokens in the response.

        Returns:
            The model's response as a string.

        Raises:
            GroqClientError: On API failure.
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise GroqClientError(f"Groq API call failed: {str(e)}")

    def chat_json(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request and parse the response as JSON.

        Returns the parsed dict, or raises GroqClientError if parsing fails.
        """
        raw = self.chat(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last fence lines
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise GroqClientError(
                f"Failed to parse LLM response as JSON: {e}\nRaw response:\n{raw}"
            )

    def multi_turn_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> str:
        """
        Send a multi-turn conversation to Groq.

        Args:
            messages: List of {"role": "...", "content": "..."} dicts.

        Returns:
            The model's response as a string.
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise GroqClientError(f"Groq API call failed: {str(e)}")
