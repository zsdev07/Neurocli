"""
Config manager — loads/saves keys and preferences from ~/.neurocli/config.json
"""

import os
import json
from pathlib import Path

CONFIG_DIR  = Path.home() / ".neurocli"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE= CONFIG_DIR / "history.json"
VECTOR_DIR  = CONFIG_DIR / "vectors"

DEFAULT_CONFIG = {
    "provider": "groq",
    "model": "llama-3.3-70b-versatile",
    "providers": {
        "openai":     {"api_key": "", "model": "gpt-4o-mini"},
        "anthropic":  {"api_key": "", "model": "claude-3-5-haiku-20241022"},
        "groq":       {"api_key": "", "model": "llama-3.3-70b-versatile"},
        "gemini":     {"api_key": "", "model": "gemini-2.0-flash"},
        "openrouter": {"api_key": "", "model": "mistralai/mistral-7b-instruct"},
        "ollama":     {"base_url": "http://localhost:11434", "model": "llama3"}
    },
    "search": {
        "engine": "duckduckgo",
        "tavily_api_key": ""
    },
    "git": {
        "auto_commit": False,
        "commit_prefix": "neurocli: "
    },
    "ui": {
        "theme": "midnight",
        "stream": True,
        "max_tokens": 4096
    },
    "vector": {
        "enabled": False,
        "chunk_size": 500,
        "top_k": 4
    }
}


def ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_dirs()
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE) as f:
            data = json.load(f)
        # Deep-merge with defaults so new keys always exist
        merged = _deep_merge(DEFAULT_CONFIG, data)
        return merged
    except Exception:
        return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    ensure_dirs()
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def get_active_provider_cfg(cfg: dict) -> dict:
    provider = cfg.get("provider", "groq")
    return cfg["providers"].get(provider, {})
