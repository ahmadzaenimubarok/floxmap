"""floxmap config — manage LLM credentials."""

import os
import getpass
from pathlib import Path

import yaml

FLOXMAP_HOME = Path.home() / ".floxmap"
CONFIG_PATH = FLOXMAP_HOME / "config.yaml"

ENV_MAP = {
    "api_key": "FLOXMAP_API_KEY",
    "model": "FLOXMAP_MODEL",
    "base_url": "FLOXMAP_BASE_URL",
}

DEFAULTS = {
    "provider": "openrouter",
    "model": "tencent/hy3:free",
    "api_key": "",
    "base_url": "https://openrouter.ai/api/v1",
}


def _load() -> dict:
    if not CONFIG_PATH.exists():
        return {"llm": dict(DEFAULTS)}
    with open(CONFIG_PATH) as f:
        data = yaml.safe_load(f) or {}
    return data


def _save(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


def _env_override(key: str) -> str | None:
    env_var = ENV_MAP.get(key)
    if env_var:
        return os.environ.get(env_var)
    return None


def get_config() -> dict:
    data = _load()
    llm = data.get("llm", {})
    result = {}
    for key in DEFAULTS:
        env_val = _env_override(key)
        result[key] = env_val if env_val else llm.get(key, DEFAULTS[key])
    return result


def get_masked() -> dict:
    cfg = get_config()
    masked = dict(cfg)
    if masked.get("api_key"):
        key = masked["api_key"]
        masked["api_key"] = key[:4] + "****" + key[-4:] if len(key) > 8 else "****"
    return masked


def config_set_interactive() -> None:
    current = get_config()
    prompts = {
        "provider": ("LLM provider", current["provider"]),
        "model": ("Model name", current["model"]),
        "api_key": ("API key", None),
        "base_url": ("Base URL", current["base_url"]),
    }

    data = _load()
    llm = data.setdefault("llm", {})

    for key, (label, default) in prompts.items():
        if key == "api_key":
            val = getpass.getpass(f"  {label} [{default or 'sk-xxx'}]: ").strip()
            if not val:
                val = current["api_key"]
        else:
            val = input(f"  {label} [{default}]: ").strip()
            if not val:
                val = default
        llm[key] = val

    _save(data)
    print("Config saved.")


def config_set_partial(**kwargs) -> None:
    data = _load()
    llm = data.setdefault("llm", {})
    for key, val in kwargs.items():
        if val is not None:
            llm[key] = val
    _save(data)
    print("Config updated.")
