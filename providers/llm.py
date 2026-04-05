"""
Provider router — unified interface for all LLM backends.
Supports: OpenAI, Anthropic, Groq, Gemini, OpenRouter, Ollama
"""

from __future__ import annotations
import json
from typing import Iterator, List, Dict, Any


# ─── Base ─────────────────────────────────────────────────────────────────────

class BaseProvider:
    name = "base"

    def chat(self, messages: List[Dict], model: str, stream: bool, max_tokens: int) -> str | Iterator[str]:
        raise NotImplementedError

    def list_models(self) -> list[str]:
        return []


# ─── OpenAI-compatible (also covers OpenRouter) ───────────────────────────────

class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

    def chat(self, messages, model, stream=True, max_tokens=4096):
        resp = self.client.chat.completions.create(
            model=model, messages=messages, stream=stream, max_tokens=max_tokens
        )
        if stream:
            def _gen():
                for chunk in resp:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
            return _gen()
        return resp.choices[0].message.content

    def list_models(self):
        try:
            return [m.id for m in self.client.models.list()]
        except Exception:
            return []


class OpenRouterProvider(OpenAIProvider):
    name = "openrouter"

    def __init__(self, api_key: str):
        super().__init__(api_key, base_url="https://openrouter.ai/api/v1")


# ─── Anthropic ────────────────────────────────────────────────────────────────

class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self, api_key: str):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self._anthropic = anthropic
        except ImportError:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

    def chat(self, messages, model, stream=True, max_tokens=4096):
        # Separate system prompt
        system = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                filtered.append(m)

        kwargs = dict(model=model, max_tokens=max_tokens, messages=filtered)
        if system:
            kwargs["system"] = system

        if stream:
            def _gen():
                with self.client.messages.stream(**kwargs) as s:
                    for text in s.text_stream:
                        yield text
            return _gen()
        resp = self.client.messages.create(**kwargs)
        return resp.content[0].text


# ─── Groq ─────────────────────────────────────────────────────────────────────

class GroqProvider(BaseProvider):
    name = "groq"

    def __init__(self, api_key: str):
        try:
            from groq import Groq
            self.client = Groq(api_key=api_key)
        except ImportError:
            raise RuntimeError("groq package not installed. Run: pip install groq")

    def chat(self, messages, model, stream=True, max_tokens=4096):
        resp = self.client.chat.completions.create(
            model=model, messages=messages, stream=stream, max_tokens=max_tokens
        )
        if stream:
            def _gen():
                for chunk in resp:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
            return _gen()
        return resp.choices[0].message.content


# ─── Gemini ───────────────────────────────────────────────────────────────────

class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, api_key: str):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._genai = genai
        except ImportError:
            raise RuntimeError("google-generativeai not installed. Run: pip install google-generativeai")

    def chat(self, messages, model, stream=True, max_tokens=4096):
        gemini_model = self._genai.GenerativeModel(model)
        # Convert messages to Gemini format
        history = []
        last_user = ""
        for m in messages:
            if m["role"] == "system":
                continue
            role = "user" if m["role"] == "user" else "model"
            history.append({"role": role, "parts": [m["content"]]})
        # Last user message
        if history and history[-1]["role"] == "user":
            last_user = history[-1]["parts"][0]
            history = history[:-1]

        chat = gemini_model.start_chat(history=history)
        gen_cfg = self._genai.types.GenerationConfig(max_output_tokens=max_tokens)
        resp = chat.send_message(last_user, generation_config=gen_cfg, stream=stream)

        if stream:
            def _gen():
                for chunk in resp:
                    if chunk.text:
                        yield chunk.text
            return _gen()
        return resp.text


# ─── Ollama (local) ───────────────────────────────────────────────────────────

class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    def chat(self, messages, model, stream=True, max_tokens=4096):
        import urllib.request
        payload = json.dumps({"model": model, "messages": messages, "stream": stream}).encode()
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        if stream:
            def _gen():
                with urllib.request.urlopen(req, timeout=120) as resp:
                    for line in resp:
                        line = line.strip()
                        if line:
                            try:
                                obj = json.loads(line)
                                msg = obj.get("message", {}).get("content", "")
                                if msg:
                                    yield msg
                            except Exception:
                                pass
            return _gen()
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return data.get("message", {}).get("content", "")

    def list_models(self):
        try:
            import urllib.request
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=5) as r:
                data = json.loads(r.read())
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []


# ─── Factory ──────────────────────────────────────────────────────────────────

def build_provider(cfg: dict, provider_name: str) -> BaseProvider:
    pcfg = cfg["providers"].get(provider_name, {})
    key  = pcfg.get("api_key", "")

    if provider_name == "openai":
        if not key:
            raise ValueError("OpenAI API key not set. Use /setkey openai <key>")
        return OpenAIProvider(key)

    elif provider_name == "anthropic":
        if not key:
            raise ValueError("Anthropic API key not set. Use /setkey anthropic <key>")
        return AnthropicProvider(key)

    elif provider_name == "groq":
        if not key:
            raise ValueError("Groq API key not set. Use /setkey groq <key>")
        return GroqProvider(key)

    elif provider_name == "gemini":
        if not key:
            raise ValueError("Gemini API key not set. Use /setkey gemini <key>")
        return GeminiProvider(key)

    elif provider_name == "openrouter":
        if not key:
            raise ValueError("OpenRouter API key not set. Use /setkey openrouter <key>")
        return OpenRouterProvider(key)

    elif provider_name == "ollama":
        base_url = pcfg.get("base_url", "http://localhost:11434")
        return OllamaProvider(base_url)

    else:
        raise ValueError(f"Unknown provider: {provider_name}")
