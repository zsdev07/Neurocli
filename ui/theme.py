"""
NeuroCLI Terminal UI — Midnight Black glassmorphism-inspired theme
Uses Rich for all rendering; works great in Termux.
"""

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich.rule import Rule
from rich import box
import time

# ─── Theme Definition ────────────────────────────────────────────────────────

MIDNIGHT_THEME = Theme({
    "primary":    "bold #7C3AED",
    "secondary":  "bold #06B6D4",
    "accent":     "bold #F59E0B",
    "success":    "bold #10B981",
    "error":      "bold #EF4444",
    "warning":    "#F59E0B",
    "muted":      "dim #6B7280",
    "user_msg":   "bold #A78BFA",
    "ai_msg":     "#E2E8F0",
    "tool_call":  "italic #34D399",
    "separator":  "#374151",
    "info":       "#60A5FA",
})

console = Console(theme=MIDNIGHT_THEME, highlight=True)


# ─── Banner ───────────────────────────────────────────────────────────────────

BANNER = r"""
  ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗  ██████╗██╗     ██╗
  ████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗██╔════╝██║     ██║
  ██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║██║     ██║     ██║
  ██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██║     ██║     ██║
  ██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝╚██████╗███████╗██║
  ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝╚═╝
"""


def print_banner(version: str, provider: str, model: str):
    console.print(f"[primary]{BANNER}[/primary]")
    console.print(
        Panel(
            f"[secondary]v{version}[/secondary]  ·  "
            f"[muted]provider:[/muted] [accent]{provider}[/accent]  ·  "
            f"[muted]model:[/muted] [accent]{model}[/accent]\n"
            f"[muted]Type [/muted][secondary]/help[/secondary][muted] for commands  ·  "
            f"[secondary]Ctrl+C[/secondary][muted] or [secondary]/exit[/secondary][muted] to quit[/muted]",
            border_style="primary",
            box=box.ROUNDED,
        )
    )


def print_help():
    table = Table(
        title="[primary]NeuroCLI Commands[/primary]",
        box=box.ROUNDED,
        border_style="primary",
        show_header=True,
        header_style="secondary",
    )
    table.add_column("Command", style="accent", no_wrap=True)
    table.add_column("Description", style="ai_msg")

    cmds = [
        ("/help",              "Show this help panel"),
        ("/exit  /quit",       "Exit NeuroCLI"),
        ("/clear",             "Clear conversation history"),
        ("/model [name]",      "Switch model (e.g. /model gpt-4o)"),
        ("/provider [name]",   "Switch provider (openai/anthropic/groq/gemini/openrouter/ollama)"),
        ("/keys",              "Show current API key status"),
        ("/setkey [p] [key]",  "Set an API key for a provider"),
        ("/search [query]",    "Web search (DuckDuckGo or Tavily)"),
        ("/read [path]",       "Read a file into context"),
        ("/write [path]",      "Write last AI response to file"),
        ("/run [cmd]",         "Run a shell command, output to context"),
        ("/git status",        "Show git status"),
        ("/git commit [msg]",  "Stage all & commit with message"),
        ("/git diff",          "Show git diff"),
        ("/index [path]",      "Index a file/folder for vector search"),
        ("/recall [query]",    "Semantic search over indexed docs"),
        ("/config",            "Show current config"),
        ("/stream on|off",     "Toggle streaming responses"),
        ("/system [prompt]",   "Set a custom system prompt"),
    ]
    for cmd, desc in cmds:
        table.add_row(cmd, desc)

    console.print(table)


# ─── Message rendering ────────────────────────────────────────────────────────

def print_user_msg(text: str):
    console.print(f"\n[user_msg]  You [/user_msg][muted]›[/muted] {text}")


def print_ai_header(provider: str, model: str):
    console.print(
        f"\n[secondary]  {provider}[/secondary][muted] / [/muted][accent]{model}[/accent] [muted]›[/muted]"
    )


def print_ai_chunk(chunk: str):
    """Print a streaming chunk without newline."""
    console.print(chunk, end="", markup=False, highlight=False)


def print_ai_response(text: str):
    """Render full response as Markdown."""
    md = Markdown(text)
    console.print(md)


def print_tool_call(tool: str, detail: str = ""):
    console.print(f"  [tool_call]⚙  {tool}[/tool_call][muted] {detail}[/muted]")


def print_success(msg: str):
    console.print(f"  [success]✔  {msg}[/success]")


def print_error(msg: str):
    console.print(f"  [error]✘  {msg}[/error]")


def print_warning(msg: str):
    console.print(f"  [warning]⚠  {msg}[/warning]")


def print_info(msg: str):
    console.print(f"  [info]ℹ  {msg}[/info]")


def print_rule(label: str = ""):
    console.print(Rule(label, style="separator"))


def print_code(code: str, lang: str = "python"):
    syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
    console.print(syntax)


def spinner(label: str = "Thinking…"):
    return Progress(
        SpinnerColumn(style="primary"),
        TextColumn(f"[muted]{label}[/muted]"),
        transient=True,
        console=console,
    )


def confirm(prompt: str) -> bool:
    return Confirm.ask(f"[warning]{prompt}[/warning]", console=console)


def prompt_input(label: str = "You") -> str:
    return Prompt.ask(f"\n[user_msg]{label}[/user_msg]", console=console)


def print_key_status(providers: dict):
    table = Table(
        title="[primary]API Key Status[/primary]",
        box=box.SIMPLE_HEAVY,
        border_style="separator",
        header_style="secondary",
    )
    table.add_column("Provider", style="accent")
    table.add_column("Model", style="ai_msg")
    table.add_column("Key", style="muted")
    for name, cfg in providers.items():
        key = cfg.get("api_key", "") or cfg.get("base_url", "")
        status = "[success]✔ set[/success]" if key else "[error]✘ missing[/error]"
        model  = cfg.get("model", cfg.get("base_url", "—"))
        table.add_row(name, model, status)
    console.print(table)
