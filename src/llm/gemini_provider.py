"""Gemini LLM Provider implementation with retries and structured output."""

import json
import logging
import os
import time
from typing import Any, Dict, Optional

from src.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini client supporting 1.5-flash / 2.0-flash with structured output."""

    def __init__(self, model: str = "gemini-1.5-flash", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=self.api_key)
                    self._client = genai.GenerativeModel(self.model)
                except ImportError:
                    raise ImportError("Gemini library not installed. Install google-genai")
        return self._client

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> str:
        client = self._get_client()
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        for attempt in range(3):
            try:
                if hasattr(client, "models"):
                    response = client.models.generate_content(
                        model=self.model,
                        contents=full_prompt,
                    )
                    return response.text or ""
                else:
                    response = client.generate_content(full_prompt)
                    return response.text or ""
            except Exception as e:
                logger.warning("Gemini API call attempt %d failed: %s", attempt + 1, e)
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
            prompt=prompt + "\nReturn ONLY valid JSON matching the requested schema without formatting markdown.",
            system_prompt=system_prompt,
            temperature=temperature,
        )
        clean_raw = raw.strip()
        if clean_raw.startswith("```json"):
            clean_raw = clean_raw[7:]
        if clean_raw.startswith("```"):
            clean_raw = clean_raw[3:]
        if clean_raw.endswith("```"):
            clean_raw = clean_raw[:-3]
        clean_raw = clean_raw.strip()

        return json.loads(clean_raw)
