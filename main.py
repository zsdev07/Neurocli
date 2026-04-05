#!/usr/bin/env python3
"""
NeuroCLI — Lightweight AI terminal assistant
Supports: OpenAI, Anthropic, Groq, Gemini, OpenRouter, Ollama (local)
"""

import sys
import os

# Ensure the app root is on sys.path for ALL sub-package imports
# (providers/, tools/, vector/, ui/ are all top-level siblings)
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Also patch into the environment so child processes inherit it
os.environ["PYTHONPATH"] = _ROOT + os.pathsep + os.environ.get("PYTHONPATH", "")

from neurocli.app import NeuroCLI

def main():
    app = NeuroCLI()
    app.run()

if __name__ == "__main__":
    main()
