"""
File tools — read, write, list directory
"""

from __future__ import annotations
import os
from pathlib import Path


def read_file(path: str) -> str:
    """Read a file and return its contents with metadata header."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if p.is_dir():
        return _list_dir(p)
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
        size = p.stat().st_size
        lines = text.count("\n")
        header = f"[File: {p}  |  {size} bytes  |  {lines} lines]\n\n"
        # Truncate very large files
        if len(text) > 50_000:
            text = text[:50_000] + f"\n\n[... truncated — {len(text)-50_000} more chars ...]"
        return header + text
    except Exception as e:
        raise IOError(f"Cannot read {path}: {e}")


def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent dirs as needed."""
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written {len(content)} chars to {p}"


def _list_dir(p: Path, depth: int = 2) -> str:
    lines = [f"[Directory: {p}]\n"]

    def _walk(d: Path, indent: int, remaining: int):
        if remaining <= 0:
            lines.append("  " * indent + "...")
            return
        try:
            entries = sorted(d.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        except PermissionError:
            return
        for e in entries:
            prefix = "  " * indent
            if e.is_dir():
                lines.append(f"{prefix}📁 {e.name}/")
                _walk(e, indent + 1, remaining - 1)
            else:
                size = e.stat().st_size
                lines.append(f"{prefix}📄 {e.name}  [{size}B]")

    _walk(p, 0, depth)
    return "\n".join(lines)


def append_file(path: str, content: str) -> str:
    """Append content to a file."""
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(content)
    return f"Appended {len(content)} chars to {p}"
