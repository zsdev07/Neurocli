"""
NeuroCLI App — main REPL loop + command dispatcher
"""

from __future__ import annotations
import os
import sys
from typing import List, Dict

from neurocli.config import (
    load_config, save_config, get_active_provider_cfg,
    CONFIG_FILE
)
from providers.llm import build_provider
from tools.search import search
from tools.files import read_file, write_file
from tools.git import git_status, git_diff, git_log, git_commit, git_push, run_shell
from vector.index import index_path, recall, index_stats, clear_index
from ui.theme import (
    console, print_banner, print_help, print_user_msg,
    print_ai_header, print_ai_chunk, print_ai_response,
    print_tool_call, print_success, print_error, print_warning,
    print_info, print_rule, print_code, spinner, confirm,
    prompt_input, print_key_status
)

VERSION = "1.0.0"

DEFAULT_SYSTEM = (
    "You are NeuroCLI, a highly capable AI assistant running in the terminal. "
    "Be concise and technical. Use markdown formatting when it aids clarity. "
    "When writing code, always specify the language in fenced code blocks."
)


class NeuroCLI:
    def __init__(self):
        self.cfg = load_config()
        self.history: List[Dict] = []
        self.system_prompt = DEFAULT_SYSTEM
        self.last_response = ""
        self.provider = None
        self._init_provider()

    # ─── Provider init ────────────────────────────────────────────────────────

    def _init_provider(self):
        try:
            self.provider = build_provider(self.cfg, self.cfg["provider"])
        except Exception as e:
            print_warning(f"Provider not ready: {e}")
            self.provider = None

    def _active_model(self) -> str:
        pcfg = get_active_provider_cfg(self.cfg)
        return pcfg.get("model", "unknown")

    # ─── Entry point ─────────────────────────────────────────────────────────

    def run(self):
        print_banner(VERSION, self.cfg["provider"], self._active_model())
        while True:
            try:
                raw = prompt_input("You")
            except (KeyboardInterrupt, EOFError):
                print_info("Bye!")
                break

            raw = raw.strip()
            if not raw:
                continue

            if raw.startswith("/"):
                self._dispatch_command(raw)
            else:
                self._chat(raw)

    # ─── Command dispatcher ───────────────────────────────────────────────────

    def _dispatch_command(self, raw: str):
        parts = raw.split(None, 2)
        cmd   = parts[0].lower()
        arg1  = parts[1] if len(parts) > 1 else ""
        arg2  = parts[2] if len(parts) > 2 else ""

        if cmd in ("/exit", "/quit", "/q"):
            print_info("Bye!")
            sys.exit(0)

        elif cmd == "/help":
            print_help()

        elif cmd == "/clear":
            self.history.clear()
            print_success("History cleared.")

        elif cmd == "/config":
            import json
            print_code(json.dumps(self.cfg, indent=2), "json")

        elif cmd == "/keys":
            print_key_status(self.cfg["providers"])

        elif cmd == "/setkey":
            self._cmd_setkey(arg1, arg2)

        elif cmd == "/provider":
            self._cmd_provider(arg1)

        elif cmd == "/model":
            self._cmd_model(arg1)

        elif cmd == "/stream":
            self._cmd_stream(arg1)

        elif cmd == "/system":
            rest = raw[len("/system"):].strip()
            if rest:
                self.system_prompt = rest
                print_success(f"System prompt updated.")
            else:
                print_info(f"Current system: {self.system_prompt}")

        elif cmd == "/search":
            self._cmd_search(raw[len("/search"):].strip())

        elif cmd == "/read":
            self._cmd_read(arg1)

        elif cmd == "/write":
            self._cmd_write(arg1)

        elif cmd == "/run":
            self._cmd_run(raw[len("/run"):].strip())

        elif cmd == "/git":
            self._cmd_git(arg1, arg2, raw)

        elif cmd == "/index":
            self._cmd_index(arg1)

        elif cmd == "/recall":
            self._cmd_recall(raw[len("/recall"):].strip())

        elif cmd == "/indexstats":
            print_info(index_stats())

        elif cmd == "/clearindex":
            if confirm("Clear the entire vector index?"):
                print_success(clear_index())

        else:
            print_error(f"Unknown command: {cmd}. Type /help for options.")

    # ─── Individual commands ──────────────────────────────────────────────────

    def _cmd_setkey(self, provider: str, key: str):
        if not provider or not key:
            print_error("Usage: /setkey <provider> <api_key>")
            return
        provider = provider.lower()
        if provider not in self.cfg["providers"]:
            print_error(f"Unknown provider: {provider}")
            return
        if provider == "ollama":
            self.cfg["providers"][provider]["base_url"] = key
        else:
            self.cfg["providers"][provider]["api_key"] = key
        save_config(self.cfg)
        print_success(f"Key saved for {provider}.")
        # Re-init if this is the active provider
        if self.cfg["provider"] == provider:
            self._init_provider()

    def _cmd_provider(self, name: str):
        if not name:
            print_info(f"Current provider: {self.cfg['provider']}")
            return
        name = name.lower()
        if name not in self.cfg["providers"]:
            print_error(f"Unknown provider: {name}. Choose from: {', '.join(self.cfg['providers'])}")
            return
        self.cfg["provider"] = name
        save_config(self.cfg)
        self._init_provider()
        if self.provider:
            print_success(f"Switched to {name} / {self._active_model()}")

    def _cmd_model(self, model: str):
        if not model:
            print_info(f"Current model: {self._active_model()}")
            return
        provider = self.cfg["provider"]
        self.cfg["providers"][provider]["model"] = model
        save_config(self.cfg)
        print_success(f"Model set to {model} for {provider}.")

    def _cmd_stream(self, val: str):
        if val.lower() in ("on", "1", "true", "yes"):
            self.cfg["ui"]["stream"] = True
            save_config(self.cfg)
            print_success("Streaming enabled.")
        elif val.lower() in ("off", "0", "false", "no"):
            self.cfg["ui"]["stream"] = False
            save_config(self.cfg)
            print_success("Streaming disabled.")
        else:
            current = self.cfg["ui"].get("stream", True)
            print_info(f"Streaming is {'on' if current else 'off'}. Use /stream on|off")

    def _cmd_search(self, query: str):
        if not query:
            print_error("Usage: /search <query>")
            return
        print_tool_call("web_search", query)
        with spinner("Searching…"):
            pass
        try:
            result = search(query, self.cfg)
            console.print(result)
            # Inject into next chat context
            self.history.append({"role": "user", "content": f"[Search Results]\n{result}"})
            self.history.append({"role": "assistant", "content": "I've retrieved those search results. What would you like to know?"})
        except Exception as e:
            print_error(str(e))

    def _cmd_read(self, path: str):
        if not path:
            print_error("Usage: /read <path>")
            return
        print_tool_call("read_file", path)
        try:
            content = read_file(path)
            # Inject as context
            self.history.append({
                "role": "user",
                "content": f"I'm sharing this file with you:\n\n{content}"
            })
            self.history.append({
                "role": "assistant",
                "content": f"Got it — I've read `{path}`. Ask me anything about it."
            })
            print_success(f"File loaded into context: {path}")
        except Exception as e:
            print_error(str(e))

    def _cmd_write(self, path: str):
        if not path:
            print_error("Usage: /write <path>")
            return
        if not self.last_response:
            print_error("No AI response to write yet.")
            return
        try:
            msg = write_file(path, self.last_response)
            print_success(msg)
        except Exception as e:
            print_error(str(e))

    def _cmd_run(self, cmd: str):
        if not cmd:
            print_error("Usage: /run <shell command>")
            return
        print_tool_call("shell", cmd)
        output = run_shell(cmd)
        console.print(output)
        self.history.append({"role": "user", "content": f"[Shell output of `{cmd}`]\n{output}"})
        self.history.append({"role": "assistant", "content": "I've seen the command output. What would you like to do with it?"})

    def _cmd_git(self, sub: str, arg: str, raw: str):
        sub = sub.lower()
        if sub == "status":
            print_tool_call("git", "status")
            print(git_status())
        elif sub == "diff":
            print_tool_call("git", "diff")
            staged = "staged" in raw
            print(git_diff(staged=staged))
        elif sub == "log":
            print_tool_call("git", "log")
            print(git_log())
        elif sub == "commit":
            msg = arg or raw.split(None, 2)[2] if len(raw.split(None, 2)) > 2 else ""
            if not msg:
                print_error("Usage: /git commit <message>")
                return
            prefix = self.cfg["git"].get("commit_prefix", "")
            print_tool_call("git", f"commit: {msg}")
            result = git_commit(msg, prefix=prefix)
            print(result)
        elif sub == "push":
            print_tool_call("git", "push")
            print(git_push())
        else:
            print_info("Git commands: /git status | /git diff | /git log | /git commit <msg> | /git push")

    def _cmd_index(self, path: str):
        if not path:
            print_error("Usage: /index <file_or_dir>")
            return
        print_tool_call("vector_index", path)
        chunk_size = self.cfg["vector"].get("chunk_size", 500)
        with spinner("Indexing…"):
            pass
        result = index_path(path, chunk_size)
        print_success(result)

    def _cmd_recall(self, query: str):
        if not query:
            print_error("Usage: /recall <query>")
            return
        print_tool_call("vector_recall", query)
        top_k = self.cfg["vector"].get("top_k", 4)
        result = recall(query, top_k)
        console.print(result)
        # Inject into history
        self.history.append({"role": "user", "content": f"[Vector recall]\n{result}"})
        self.history.append({"role": "assistant", "content": "I've retrieved those document excerpts. What would you like to know?"})

    # ─── Core chat ────────────────────────────────────────────────────────────

    def _chat(self, user_input: str):
        if not self.provider:
            print_error("No provider configured. Use /setkey and /provider first. Type /help.")
            return

        print_user_msg(user_input)
        self.history.append({"role": "user", "content": user_input})

        messages = [{"role": "system", "content": self.system_prompt}] + self.history

        stream    = self.cfg["ui"].get("stream", True)
        max_tok   = self.cfg["ui"].get("max_tokens", 4096)
        model     = self._active_model()
        provider_name = self.cfg["provider"]

        print_ai_header(provider_name, model)

        try:
            response_text = ""
            result = self.provider.chat(messages, model, stream=stream, max_tokens=max_tok)

            if stream:
                for chunk in result:
                    print_ai_chunk(chunk)
                    response_text += chunk
                console.print()  # newline after stream
            else:
                with spinner("Thinking…") as prog:
                    prog.add_task("")
                response_text = result
                print_ai_response(response_text)

            self.history.append({"role": "assistant", "content": response_text})
            self.last_response = response_text

            # Auto-commit if enabled
            if self.cfg["git"].get("auto_commit") and response_text:
                short = user_input[:50].replace("\n", " ")
                git_commit(f"chat: {short}", prefix=self.cfg["git"].get("commit_prefix",""))

        except KeyboardInterrupt:
            console.print()
            print_warning("Response interrupted.")
        except Exception as e:
            print_error(f"LLM error: {e}")
            # Remove the failed user message from history
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()
