# NeuroCLI 

**Lightweight, powerful AI terminal assistant — works everywhere, including Termux.**

Multi-provider · Web Search · File R/W · Git · Vector RAG · Beautiful TUI

---

## Features

| Feature | Details |
|---|---|
| **LLM Providers** | OpenAI, Anthropic, Groq, Gemini, OpenRouter, Ollama (local) |
| **Web Search** | DuckDuckGo (no key) + Tavily (API key optional) |
| **File Tools** | Read, write, list files — inject into context |
| **Git** | status, diff, log, commit, push — auto-commit option |
| **Shell** | Run any command, output piped to context |
| **Vector RAG** | Index files/folders, semantic recall for long chats |
| **Streaming** | Real-time token streaming from all providers |
| **Termux** | First-class support — tested on Android |
| **Config** | Persistent JSON config in `~/.neurocli/config.json` |

---

## Install

### Linux / macOS / Windows (WSL)

```bash
git clone <repo>
cd neurocli
pip install rich groq          # minimum: rich + one provider
python main.py
```

### Termux (Android)

```bash
# 1. Install Termux from F-Droid (not Play Store)
# 2. Open Termux and run:
bash install_termux.sh
```

Or manually:
```bash
pkg update && pkg install python git
pip install rich groq
python main.py
```

---

## Quick Start

```
$ python main.py

  [NeuroCLI banner]

You › /setkey groq gsk_xxxxxxxxxxxxxxxx
  ✔  Key saved for groq.

You › /provider groq
  ✔  Switched to groq / llama-3.3-70b-versatile

You › What is the Fibonacci sequence?
  groq / llama-3.3-70b-versatile ›
  The Fibonacci sequence is...
```

---

## All Commands

### Chat & Session
| Command | Description |
|---|---|
| `<any text>` | Chat with the AI |
| `/clear` | Clear conversation history |
| `/system <prompt>` | Override the system prompt |
| `/stream on\|off` | Toggle streaming |
| `/exit` or `/quit` | Exit NeuroCLI |

### Provider & Model
| Command | Description |
|---|---|
| `/provider <name>` | Switch provider (openai/anthropic/groq/gemini/openrouter/ollama) |
| `/model <name>` | Switch model for current provider |
| `/setkey <provider> <key>` | Save an API key |
| `/keys` | Show API key status for all providers |
| `/config` | Show full config JSON |

### Tools
| Command | Description |
|---|---|
| `/search <query>` | Web search (DDG or Tavily), injects results into context |
| `/read <path>` | Read a file or directory into context |
| `/write <path>` | Write last AI response to a file |
| `/run <command>` | Run a shell command, output into context |

### Git
| Command | Description |
|---|---|
| `/git status` | Show `git status` |
| `/git diff` | Show unstaged diff |
| `/git diff staged` | Show staged diff |
| `/git log` | Show last 10 commits |
| `/git commit <msg>` | Stage all + commit |
| `/git push` | Push to remote |

### Vector RAG
| Command | Description |
|---|---|
| `/index <path>` | Index a file or directory for semantic search |
| `/recall <query>` | Search indexed docs, inject top results into context |
| `/indexstats` | Show index size |
| `/clearindex` | Clear the entire index |

---

## Providers

### Groq (Recommended for Termux)
Free tier, fastest inference, no credit card needed.
```
/setkey groq gsk_xxxxxxxxxxxx
/provider groq
/model llama-3.3-70b-versatile
```
Get key: https://console.groq.com

### OpenAI
```
/setkey openai sk-xxxxxxxxxxxx
/provider openai
/model gpt-4o-mini
```

### Anthropic
```
/setkey anthropic sk-ant-xxxxxxxxxxxx
/provider anthropic
/model claude-3-5-haiku-20241022
```

### Gemini
```
/setkey gemini AIzaXXXXXXXXXXXX
/provider gemini
/model gemini-2.0-flash
```

### OpenRouter (any model via one key)
```
/setkey openrouter sk-or-xxxxxxxxxxxx
/provider openrouter
/model mistralai/mistral-7b-instruct
```
Browse models: https://openrouter.ai/models

### Ollama (local, no key)
```bash
# Start Ollama first:
ollama run llama3
```
```
/provider ollama
/model llama3
```

---

## Web Search

**DuckDuckGo** (default, no key required):
```
/search latest news on Rust programming language
```

**Tavily** (higher quality, requires key):
```
/setkey tavily tvly-xxxxxxxxxxxx    # saved separately in search config
```
Then set engine in config:
```json
"search": { "engine": "tavily", "tavily_api_key": "tvly-..." }
```
Or edit `~/.neurocli/config.json` directly.

---

## Vector RAG (Long Context)

Index your codebase or docs:
```
/index ~/myproject/src
/index ~/notes/
```

Ask questions:
```
/recall how does authentication work
/recall database schema
```
Results are injected into context before your next message.

---

## File Layout

```
neurocli/
├── main.py                  # Entry point
├── setup.py                 # Package install
├── requirements.txt
├── install_termux.sh        # One-click Termux install
├── neurocli/
│   ├── __init__.py
│   ├── app.py               # Main REPL + command dispatcher
│   └── config.py            # Config load/save
├── providers/
│   ├── __init__.py
│   └── llm.py               # All LLM provider adapters
├── tools/
│   ├── __init__.py
│   ├── search.py            # DuckDuckGo + Tavily
│   ├── files.py             # Read/write files
│   └── git.py               # Git + shell commands
├── vector/
│   ├── __init__.py
│   └── index.py             # TF-IDF vector store (no deps)
└── ui/
    ├── __init__.py
    └── theme.py             # Rich TUI — Midnight Black theme
```

Config is stored at: `~/.neurocli/config.json`
Vector index at: `~/.neurocli/vectors/index.json`

---

## Testing in Termux — Step by Step

```bash
# Step 1: Install Termux (F-Droid version recommended)
# Step 2: Open Termux

# Step 3: Update & install deps
pkg update && pkg upgrade -y
pkg install python git

# Step 4: Clone or copy neurocli
# If you have the zip:
pkg install unzip
unzip neurocli.zip -d neurocli
cd neurocli

# Step 5: Install Python deps
pip install rich groq           # groq is fastest free option

# Step 6: Run
python main.py

# Step 7: Set your key (get free key at console.groq.com)
# > /setkey groq gsk_xxxxxxxx

# Step 8: Chat!
# > Write a Python hello world

# Step 9: Test tools
# > /search what is the weather today
# > /read ~/storage/downloads/myfile.txt
# > /git status
```

### Termux Storage Access
To read files from your phone:
```bash
termux-setup-storage   # grants storage permission
# Then: /read ~/storage/shared/Documents/myfile.txt
```

---

## Configuration Reference

`~/.neurocli/config.json`:
```json
{
  "provider": "groq",
  "model": "llama-3.3-70b-versatile",
  "providers": {
    "openai":     { "api_key": "", "model": "gpt-4o-mini" },
    "anthropic":  { "api_key": "", "model": "claude-3-5-haiku-20241022" },
    "groq":       { "api_key": "", "model": "llama-3.3-70b-versatile" },
    "gemini":     { "api_key": "", "model": "gemini-2.0-flash" },
    "openrouter": { "api_key": "", "model": "mistralai/mistral-7b-instruct" },
    "ollama":     { "base_url": "http://localhost:11434", "model": "llama3" }
  },
  "search": {
    "engine": "duckduckgo",
    "tavily_api_key": ""
  },
  "git": {
    "auto_commit": false,
    "commit_prefix": "neurocli: "
  },
  "ui": {
    "theme": "midnight",
    "stream": true,
    "max_tokens": 4096
  },
  "vector": {
    "enabled": false,
    "chunk_size": 500,
    "top_k": 4
  }
}
```

---

## Minimum Requirements

- Python 3.8+
- `rich` (the only hard dependency)
- One LLM provider library

Works on: Linux, macOS, Windows WSL, Android (Termux), Raspberry Pi

---

## License

MIT — free to use, modify, and distribute.
