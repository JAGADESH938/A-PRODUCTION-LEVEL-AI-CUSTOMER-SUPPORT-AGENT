"""Factory for loading LLM providers based on environment or configuration."""

import os
from src.llm.base import BaseLLMProvider
from src.llm.mock_provider import MockLLMProvider
from src.llm.openai_provider import OpenAIProvider
from src.llm.gemini_provider import GeminiProvider


def get_llm_provider(
    provider_name: str = None,
    model_name: str = None,
) -> BaseLLMProvider:
    provider = (provider_name or os.getenv("LLM_PROVIDER", "mock")).lower().strip()
    model = model_name or os.getenv("LLM_MODEL", "gpt-4o-mini")

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            # Fallback to mock if API key is missing
            return MockLLMProvider(model=model)
        return OpenAIProvider(model=model, api_key=api_key)
    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            return MockLLMProvider(model=model)
        return GeminiProvider(model=model, api_key=api_key)
    else:
        return MockLLMProvider(model=model)
