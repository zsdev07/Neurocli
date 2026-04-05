"""
Vector index — lightweight local RAG using TF-IDF + cosine similarity.
No GPU, no heavy deps. Falls back gracefully if numpy unavailable.
Persists as JSON in ~/.neurocli/vectors/
"""

from __future__ import annotations
import json
import math
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple


VECTOR_DIR = Path.home() / ".neurocli" / "vectors"
INDEX_FILE  = VECTOR_DIR / "index.json"


# ─── Text utilities ───────────────────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


def _chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def _tf(tokens: List[str]) -> Dict[str, float]:
    freq: Dict[str, int] = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    total = max(len(tokens), 1)
    return {k: v / total for k, v in freq.items()}


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    keys = set(a) & set(b)
    if not keys:
        return 0.0
    dot = sum(a[k] * b[k] for k in keys)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ─── Index I/O ────────────────────────────────────────────────────────────────

def _load_index() -> List[dict]:
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    if INDEX_FILE.exists():
        try:
            return json.loads(INDEX_FILE.read_text())
        except Exception:
            pass
    return []


def _save_index(docs: List[dict]):
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(docs, indent=2))


# ─── Public API ───────────────────────────────────────────────────────────────

def index_path(path: str, chunk_size: int = 500) -> str:
    """Index a file or directory. Returns a summary string."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Path not found: {path}"

    docs = _load_index()
    added = 0

    files: List[Path] = []
    if p.is_dir():
        for ext in ["*.txt", "*.md", "*.py", "*.js", "*.ts", "*.json",
                    "*.yaml", "*.yml", "*.html", "*.css", "*.java", "*.cpp",
                    "*.c", "*.h", "*.rs", "*.go", "*.sh"]:
            files.extend(p.rglob(ext))
    else:
        files = [p]

    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        chunks = _chunk_text(text, chunk_size)
        for i, chunk in enumerate(chunks):
            tokens = _tokenize(chunk)
            if len(tokens) < 5:
                continue
            tf_vec = _tf(tokens)
            docs.append({
                "source": str(f),
                "chunk_id": i,
                "text": chunk,
                "tf": tf_vec
            })
            added += 1

    _save_index(docs)
    return f"Indexed {added} chunks from {len(files)} file(s). Total index size: {len(docs)} chunks."


def recall(query: str, top_k: int = 4) -> str:
    """Semantic search over the index. Returns formatted context string."""
    docs = _load_index()
    if not docs:
        return "Index is empty. Use /index <path> first."

    q_tokens = _tokenize(query)
    q_tf     = _tf(q_tokens)

    scored: List[Tuple[float, dict]] = []
    for doc in docs:
        sim = _cosine(q_tf, doc["tf"])
        if sim > 0:
            scored.append((sim, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    if not top:
        return f"No relevant documents found for: {query}"

    lines = [f"[Vector Recall] Query: {query}\n"]
    for rank, (score, doc) in enumerate(top, 1):
        lines.append(f"--- [{rank}] {doc['source']} (chunk {doc['chunk_id']}, score={score:.3f})")
        lines.append(doc["text"])
        lines.append("")

    return "\n".join(lines)


def index_stats() -> str:
    docs = _load_index()
    if not docs:
        return "Index is empty."
    sources = {d["source"] for d in docs}
    return f"Index: {len(docs)} chunks from {len(sources)} files."


def clear_index() -> str:
    if INDEX_FILE.exists():
        INDEX_FILE.unlink()
    return "Vector index cleared."
