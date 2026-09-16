"""OpenAI LLM Provider implementation with retries, timeout, and structured output."""

import json
import logging
import os
import time
from typing import Any, Dict, Optional

from src.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API client supporting chat models with structured JSON parsing."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("OpenAI package not installed. Run pip install openai")
        return self._client

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> str:
        client = self._get_client()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=20.0,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                logger.warning("OpenAI API call attempt %d failed: %s", attempt + 1, e)
                if attempt == 2:
                    raise
                time.sleep(1.5 ** attempt)
        return ""

    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        raw = self.generate(
            prompt=prompt + "\nReturn ONLY valid JSON matching the requested schema.",
            system_prompt=system_prompt,
            temperature=temperature,
        )
        # Strip markdown json code block if present
        clean_raw = raw.strip()
        if clean_raw.startswith("```json"):
            clean_raw = clean_raw[7:]
        if clean_raw.startswith("```"):
            clean_raw = clean_raw[3:]
        if clean_raw.endswith("```"):
            clean_raw = clean_raw[:-3]
        clean_raw = clean_raw.strip()

        return json.loads(clean_raw)
