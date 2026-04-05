"""
Git tools — wraps subprocess git commands.
Works anywhere git is available (including Termux).
"""

from __future__ import annotations
import subprocess
from pathlib import Path


def _run(args: list[str], cwd: str | None = None) -> tuple[str, str, int]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=cwd or Path.cwd(),
            timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        return "", "git not found. Install git first.", 1
    except subprocess.TimeoutExpired:
        return "", "git command timed out.", 1


def git_status(cwd: str | None = None) -> str:
    out, err, code = _run(["git", "status", "--short", "--branch"], cwd)
    if code != 0:
        return f"git error: {err.strip()}"
    return out.strip() or "Working tree clean."


def git_diff(cwd: str | None = None, staged: bool = False) -> str:
    args = ["git", "diff"]
    if staged:
        args.append("--staged")
    out, err, code = _run(args, cwd)
    if code != 0:
        return f"git error: {err.strip()}"
    if not out.strip():
        return "No changes." if staged else "No unstaged changes."
    # Limit output
    if len(out) > 8000:
        out = out[:8000] + "\n[... diff truncated ...]"
    return out


def git_log(n: int = 10, cwd: str | None = None) -> str:
    out, err, code = _run(
        ["git", "log", f"-{n}", "--oneline", "--color=never"], cwd
    )
    if code != 0:
        return f"git error: {err.strip()}"
    return out.strip() or "No commits yet."


def git_commit(message: str, cwd: str | None = None, prefix: str = "") -> str:
    full_msg = f"{prefix}{message}" if prefix else message
    # Stage all
    _, err1, c1 = _run(["git", "add", "-A"], cwd)
    if c1 != 0:
        return f"git add error: {err1.strip()}"
    out, err, code = _run(["git", "commit", "-m", full_msg], cwd)
    if code != 0:
        return f"git commit error: {err.strip()}"
    return out.strip()


def git_push(cwd: str | None = None) -> str:
    out, err, code = _run(["git", "push"], cwd)
    if code != 0:
        return f"git push error: {err.strip()}"
    return out.strip() or "Pushed successfully."


def run_shell(cmd: str, cwd: str | None = None) -> str:
    """Run an arbitrary shell command and return combined output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=cwd or Path.cwd(), timeout=60
        )
        out = result.stdout
        err = result.stderr
        combined = ""
        if out:
            combined += out
        if err:
            combined += f"\n[stderr]\n{err}"
        if not combined.strip():
            combined = f"[exited {result.returncode}]"
        if len(combined) > 10_000:
            combined = combined[:10_000] + "\n[... output truncated ...]"
        return combined.strip()
    except subprocess.TimeoutExpired:
        return "[command timed out after 60s]"
    except Exception as e:
        return f"[error] {e}"
