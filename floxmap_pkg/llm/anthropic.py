"""Anthropic native Messages API provider."""

import json
import urllib.request
import urllib.error

from floxmap_pkg.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def chat(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system,
            "messages": [
                {"role": "user", "content": user},
            ],
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            self.API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": self.API_VERSION,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode())
            return body["content"][0]["text"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            raise RuntimeError(
                f"Anthropic API error {e.code}: {error_body}"
            ) from e
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected response format: {e}") from e
