"""
Web search — DuckDuckGo (no key needed) + Tavily (paid, better quality)
"""

from __future__ import annotations
import json
import urllib.request
import urllib.parse


# ─── DuckDuckGo ───────────────────────────────────────────────────────────────

def _ddg_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Uses DuckDuckGo Lite HTML scraping (no API key required).
    Falls back to instant-answer API for quick facts.
    """
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [{"title": r.get("title",""), "url": r.get("href",""), "snippet": r.get("body","")} for r in results]
    except ImportError:
        pass

    # Fallback: DuckDuckGo Instant Answer API
    params = urllib.parse.urlencode({"q": query, "format": "json", "no_html": 1, "skip_disambig": 1})
    url = f"https://api.duckduckgo.com/?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "NeuroCLI/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            results = []
            abstract = data.get("AbstractText","")
            if abstract:
                results.append({"title": data.get("Heading",""), "url": data.get("AbstractURL",""), "snippet": abstract})
            for r in data.get("RelatedTopics", [])[:max_results-1]:
                if "Text" in r:
                    results.append({"title": r.get("Text","")[:80], "url": r.get("FirstURL",""), "snippet": r.get("Text","")})
            return results
    except Exception as e:
        return [{"title": "Error", "url": "", "snippet": str(e)}]


# ─── Tavily ───────────────────────────────────────────────────────────────────

def _tavily_search(query: str, api_key: str, max_results: int = 5) -> list[dict]:
    payload = json.dumps({
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results
    }).encode()
    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return [
                {"title": r.get("title",""), "url": r.get("url",""), "snippet": r.get("content","")}
                for r in data.get("results", [])
            ]
    except Exception as e:
        return [{"title": "Tavily Error", "url": "", "snippet": str(e)}]


# ─── Public API ───────────────────────────────────────────────────────────────

def search(query: str, cfg: dict, max_results: int = 5) -> str:
    """
    Returns formatted search results as a string to inject into context.
    Picks Tavily if key is set, otherwise DuckDuckGo.
    """
    search_cfg  = cfg.get("search", {})
    tavily_key  = search_cfg.get("tavily_api_key", "")
    engine      = search_cfg.get("engine", "duckduckgo")

    if tavily_key and engine == "tavily":
        results = _tavily_search(query, tavily_key, max_results)
        source  = "Tavily"
    else:
        results = _ddg_search(query, max_results)
        source  = "DuckDuckGo"

    if not results:
        return f"No results found for: {query}"

    lines = [f"[Web Search — {source}] Query: {query}\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. **{r['title']}**")
        if r.get("url"):
            lines.append(f"   URL: {r['url']}")
        lines.append(f"   {r['snippet']}\n")

    return "\n".join(lines)
