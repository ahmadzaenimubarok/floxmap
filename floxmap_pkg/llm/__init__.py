"""LLM provider factory."""

from floxmap_pkg.config import get_config
from floxmap_pkg.llm.base import LLMProvider
from floxmap_pkg.llm.openai_compat import OpenAICompatProvider
from floxmap_pkg.llm.anthropic import AnthropicProvider


def get_provider() -> LLMProvider:
    cfg = get_config()
    provider = cfg["provider"]
    api_key = cfg["api_key"]
    model = cfg["model"]

    if not api_key:
        raise RuntimeError(
            "No API key configured. Run: floxmap config set"
        )

    if provider == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model)
    else:
        # openai, openrouter, deepseek, groq, ollama — all use OpenAI-compat
        return OpenAICompatProvider(
            api_key=api_key,
            model=model,
            base_url=cfg["base_url"],
        )
