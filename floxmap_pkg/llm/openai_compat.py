"""OpenAI-compatible LLM provider (OpenAI, OpenRouter, DeepSeek, Groq, Ollama)."""

import json
import urllib.request
import urllib.error

from floxmap_pkg.llm.base import LLMProvider


class OpenAICompatProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def chat(self, system: str, user: str) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "floxmap/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode())
            return body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            raise RuntimeError(
                f"OpenAI-compat API error {e.code}: {error_body}"
            ) from e
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected response format: {e}") from e
