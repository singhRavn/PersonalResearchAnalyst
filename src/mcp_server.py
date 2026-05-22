"""
MCP server for EAGV3 Session 6.
 
Nine tools, stdio transport:
    search_web, fetch_url, get_time, currency_convert,
    read_file, list_dir, create_file, update_file, edit_file
    save_memory, load_memory

search_web:  DuckDuckGo only (no API key required). Hard-capped at 5 results.
fetch_url:   crawl4ai only — clean markdown via headless Chromium.
 
File tools are sandboxed under ./sandbox/. Run:  python mcp_server.py
"""
 
from __future__ import annotations
 
import json
import os
import threading
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
 
import httpx
from ddgs import DDGS
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
 
MAX_SEARCH_RESULTS = 5  # hard cap — DuckDuckGo has no strict limits but we cap for consistency
 
load_dotenv(Path(__file__).parent / ".env")
 
mcp = FastMCP("eagv3-s6-server")
 
SANDBOX = Path(__file__).parent / "sandbox"
SANDBOX.mkdir(exist_ok=True)
 
 
def _safe(path: str) -> Path:
    p = (SANDBOX / path).resolve()
    base = SANDBOX.resolve()
    if p != base and base not in p.parents:
        raise ValueError(f"Path '{path}' escapes the sandbox")
    return p
 
 
def _ddg_search(query: str, max_results: int) -> list[dict]:
    hits: list[dict] = []
    with DDGS() as ddgs:
        for backend in ("auto", "html", "lite"):
            try:
                hits = list(ddgs.text(query, max_results=max_results, backend=backend))
            except Exception:
                hits = []
            if hits:
                break
    return [
        {
            "title": h.get("title", ""),
            "url": h.get("href", ""),
            "snippet": h.get("body", ""),
        }
        for h in hits
    ]
 
 
async def _crawl4ai_fetch(url: str) -> dict:
    from crawl4ai import AsyncWebCrawler
 
    # crawl4ai uses Rich which writes via its own captured stdout reference, so
    # contextlib.redirect_stdout doesn't catch it. Redirect at the file-descriptor
    # level — crawl4ai's banner / [FETCH] / [SCRAPE] markers would otherwise
    # corrupt the MCP stdio JSON-RPC stream.
    saved_fd = os.dup(1)
    os.dup2(2, 1)
    try:
        async with AsyncWebCrawler(verbose=False) as crawler:
            r = await crawler.arun(url=url)
    finally:
        os.dup2(saved_fd, 1)
        os.close(saved_fd)
    # r.markdown is a str subclass (StringCompatibleMarkdown) that Pydantic
    # serializes as {} because its real field is private. Pull the raw string
    # out and force a plain str so FastMCP serializes correctly.
    md = r.markdown
    raw = (
        getattr(md, "raw_markdown", None)
        or getattr(md, "fit_markdown", None)
        or md
        or r.cleaned_html
        or r.html
        or ""
    )
    text = str(raw)
    return {
        "status": int(getattr(r, "status_code", None) or 200),
        "content_type": "text/markdown",
        "length_bytes": len(text.encode("utf-8")),
        "text": text,
    }
 
 
@mcp.tool()
def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Search the web using DuckDuckGo. Hard-capped at 5 results. Example: search_web("python asyncio tutorial", 3)."""
    max_results = max(1, min(max_results, MAX_SEARCH_RESULTS))
    return _ddg_search(query, max_results)
 
 
@mcp.tool()
async def fetch_url(url: str, timeout: int = 20) -> dict:
    """Fetch clean markdown from a URL via crawl4ai (headless Chromium). Example: fetch_url("https://example.com")."""
    return await _crawl4ai_fetch(url)
 
 
@mcp.tool()
def get_time(timezone: str = "UTC") -> dict:
    """Current time in a named IANA timezone. Example: get_time("Asia/Kolkata")."""
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    offset = now.utcoffset()
    offset_hours = offset.total_seconds() / 3600 if offset else 0.0
    return {
        "iso": now.isoformat(),
        "human": now.strftime("%A, %d %B %Y %H:%M:%S %Z"),
        "timezone": timezone,
        "offset_hours": offset_hours,
    }
 
 
@mcp.tool()
def currency_convert(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert money between ISO-3 currencies via frankfurter.dev. Example: currency_convert(100, "USD", "INR")."""
    f = from_currency.upper()
    t = to_currency.upper()
    url = f"https://api.frankfurter.dev/v1/latest?amount={amount}&base={f}&symbols={t}"
    with httpx.Client(timeout=20, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        data = r.json()
    converted = data["rates"][t]
    return {
        "amount": amount,
        "from": f,
        "to": t,
        "rate": converted / amount if amount else 0.0,
        "converted": converted,
        "date": data["date"],
        "source": "frankfurter.dev",
    }
 
 
@mcp.tool()
def read_file(path: str) -> dict:
    """Read a UTF-8 text file from the sandbox. Example: read_file("notes.txt")."""
    p = _safe(path)
    text = p.read_text(encoding="utf-8")
    return {
        "path": path,
        "size_bytes": p.stat().st_size,
        "content": text,
        "encoding": "utf-8",
    }
 
 
@mcp.tool()
def list_dir(path: str = ".") -> list[dict]:
    """List a directory inside the sandbox. Example: list_dir(".")."""
    p = _safe(path)
    out = []
    for child in sorted(p.iterdir()):
        is_dir = child.is_dir()
        out.append({
            "name": child.name,
            "type": "dir" if is_dir else "file",
            "size_bytes": 0 if is_dir else child.stat().st_size,
        })
    return out
 
 
@mcp.tool()
def create_file(path: str, content: str) -> dict:
    """Create a new file in the sandbox; errors if it exists. Example: create_file("hello.txt", "hi")."""
    p = _safe(path)
    if p.exists():
        raise ValueError(f"File '{path}' already exists")
    if not p.parent.exists():
        raise ValueError(f"Parent directory of '{path}' does not exist")
    p.write_text(content, encoding="utf-8")
    return {"ok": True, "path": path, "size_bytes": p.stat().st_size}
 
 
@mcp.tool()
def update_file(path: str, content: str) -> dict:
    """Overwrite an existing sandbox file. Example: update_file("hello.txt", "new body")."""
    p = _safe(path)
    if not p.exists():
        raise ValueError(f"File '{path}' does not exist")
    p.write_text(content, encoding="utf-8")
    return {"ok": True, "path": path, "size_bytes": p.stat().st_size}
 
 
@mcp.tool()
def edit_file(path: str, find: str, replace: str, replace_all: bool = False) -> dict:
    """Find-and-replace inside a sandbox file. Example: edit_file("hello.txt", "foo", "bar")."""
    p = _safe(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(find)
    if count == 0:
        raise ValueError(f"'{find}' not found in '{path}'")
    if count > 1 and not replace_all:
        raise ValueError(
            f"'{find}' occurs {count} times in '{path}'; pass replace_all=True"
        )
    new_text = text.replace(find, replace) if replace_all else text.replace(find, replace, 1)
    p.write_text(new_text, encoding="utf-8")
    replacements = count if replace_all else 1
    return {
        "ok": True,
        "path": path,
        "replacements": replacements,
        "size_bytes": p.stat().st_size,
    }
 
 
@mcp.tool()
def save_memory(key: str, value: str) -> dict:
    """Save a key-value pair to durable memory. Example: save_memory("preferred_language", "python")."""
    # Simple implementation - in a real system this would use a proper database
    # For now, we'll use a JSON file in the sandbox
    memory_file = Path(__file__).parent / "agent_memory.json"
    
    # Load existing memories
    memories = {}
    if memory_file.exists():
        try:
            memories = json.loads(memory_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            memories = {}
    
    # Save the new memory
    memories[key] = {
        "value": value,
        "created_at": datetime.now().isoformat(),
        "accessed_at": datetime.now().isoformat(),
        "access_count": 0
    }
    
    # Save back to file
    memory_file.write_text(json.dumps(memories, indent=2), encoding="utf-8")
    
    return {"ok": True, "key": key, "value": value}
 
 
@mcp.tool()
def load_memory(key: str) -> dict:
    """Load a value from durable memory by key. Example: load_memory("preferred_language")."""
    memory_file = Path(__file__).parent / "agent_memory.json"
    
    if not memory_file.exists():
        return {"ok": False, "error": "No memory found", "value": None}
    
    try:
        memories = json.loads(memory_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"ok": False, "error": "Could not read memory", "value": None}
    
    if key not in memories:
        return {"ok": False, "error": f"No memory found for key '{key}'", "value": None}
    
    # Update access tracking
    memories[key]["accessed_at"] = datetime.now().isoformat()
    memories[key]["access_count"] = memories[key].get("access_count", 0) + 1
    
    # Save back to file
    memory_file.write_text(json.dumps(memories, indent=2), encoding="utf-8")
    
    return {
        "ok": True,
        "key": key,
        "value": memories[key]["value"],
        "created_at": memories[key]["created_at"],
        "accessed_at": memories[key]["accessed_at"],
        "access_count": memories[key]["access_count"]
    }
 
 
if __name__ == "__main__":
    mcp.run(transport="stdio")