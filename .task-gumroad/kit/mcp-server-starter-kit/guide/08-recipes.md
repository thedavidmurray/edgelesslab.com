# 08 — Recipes

Ten practical MCP server ideas with implementation sketches. Each recipe includes what it does, the key tools to expose, and the core implementation pattern.

---

## Recipe 1: Local file search

**What it does:** Search files in a directory by name pattern or content. Returns matching paths with metadata.

**Tools:**
- `search_by_name(directory, pattern)` — glob matching
- `search_by_content(directory, query, file_glob)` — content search (grep-style)
- `read_file(path)` — read a specific file

**Core pattern:**
```python
import glob
import subprocess

@mcp.tool()
async def search_by_content(directory: str, query: str, file_glob: str = "**/*") -> str:
    """Search file contents using ripgrep or grep."""
    result = subprocess.run(
        ["rg", "--json", "-l", query, "--glob", file_glob, directory],
        capture_output=True, text=True, timeout=10
    )
    matches = [json.loads(line) for line in result.stdout.splitlines() if line]
    paths = [m["data"]["path"]["text"] for m in matches if m["type"] == "match"]
    return json.dumps(paths[:50])
```

See the working implementation in `examples/file-search-server/`.

---

## Recipe 2: SQLite query interface

**What it does:** Run read queries against a SQLite database. Return results as JSON.

**Tools:**
- `list_tables()` — schema discovery
- `describe_table(name)` — column names and types
- `query(sql)` — execute a SELECT statement

**Core pattern:**
```python
import sqlite3
import json

DB_PATH = os.environ["DATABASE_PATH"]

@mcp.tool()
async def query(sql: str) -> str:
    """Run a SELECT query against the database. Only SELECT is allowed."""
    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(sql)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return json.dumps(rows, default=str)
```

See the working implementation in `examples/database-query-server/`.

---

## Recipe 3: REST API proxy

**What it does:** Wrap any REST API as MCP tools. Claude can query the API without knowing the HTTP details.

**Tools:**
- `get_resource(endpoint, params)` — GET request
- `list_endpoints()` — show available endpoints with descriptions

**Core pattern:**
```python
import httpx

BASE_URL = os.environ["API_BASE_URL"]
API_KEY = os.environ["API_KEY"]

@mcp.tool()
async def get_resource(endpoint: str, params: dict = {}) -> str:
    """Fetch data from the API. endpoint is the path, e.g. '/users/42'."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}{endpoint}",
            params=params,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=10.0,
        )
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
```

See the working implementation in `examples/api-proxy-server/`.

---

## Recipe 4: Git repository inspector

**What it does:** Expose git history, diffs, and branch info as MCP tools. Useful for code review workflows.

**Tools:**
- `git_log(repo_path, limit)` — recent commits
- `git_diff(repo_path, from_ref, to_ref)` — diff between refs
- `git_status(repo_path)` — working tree status
- `git_branches(repo_path)` — list branches

**Core pattern:**
```python
import subprocess

@mcp.tool()
async def git_log(repo_path: str, limit: int = 20) -> str:
    """Show recent git commits."""
    result = subprocess.run(
        ["git", "-C", repo_path, "log",
         f"--max-count={limit}",
         "--pretty=format:%H|%an|%ai|%s"],
        capture_output=True, text=True
    )
    entries = []
    for line in result.stdout.splitlines():
        sha, author, date, subject = line.split("|", 3)
        entries.append({"sha": sha[:8], "author": author, "date": date, "subject": subject})
    return json.dumps(entries, indent=2)
```

---

## Recipe 5: Clipboard and note manager

**What it does:** Save and retrieve snippets. Claude can store output from one tool call and retrieve it in another session.

**Tools:**
- `save_note(key, content)` — persist a named note
- `get_note(key)` — retrieve by key
- `list_notes()` — all stored keys
- `delete_note(key)` — remove a note

**Core pattern:**
```python
import sqlite3

DB = sqlite3.connect(os.path.expanduser("~/.mcp-notes.db"))
DB.execute("CREATE TABLE IF NOT EXISTS notes (key TEXT PRIMARY KEY, content TEXT, updated_at TEXT)")

@mcp.tool()
async def save_note(key: str, content: str) -> str:
    """Save a named note. Overwrites if key already exists."""
    DB.execute(
        "INSERT OR REPLACE INTO notes VALUES (?, ?, datetime('now'))",
        (key, content)
    )
    DB.commit()
    return f"Saved note '{key}' ({len(content)} chars)"
```

---

## Recipe 6: System monitoring

**What it does:** Expose system metrics — CPU, memory, disk, processes — as MCP tools.

**Tools:**
- `system_stats()` — CPU, memory, disk summary
- `top_processes(n)` — top N processes by CPU or memory
- `disk_usage(path)` — disk usage for a directory

**Core pattern:**
```python
import psutil
import json

@mcp.tool()
async def system_stats() -> str:
    """Return current CPU, memory, and disk usage."""
    stats = {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory": {
            "total_gb": round(psutil.virtual_memory().total / 1e9, 1),
            "used_percent": psutil.virtual_memory().percent,
        },
        "disk": {
            "total_gb": round(psutil.disk_usage("/").total / 1e9, 1),
            "used_percent": psutil.disk_usage("/").percent,
        },
    }
    return json.dumps(stats, indent=2)
```

---

## Recipe 7: Email digest tool

**What it does:** Fetch recent emails, summarize them, and allow search. Connects to Gmail or IMAP.

**Tools:**
- `list_recent_emails(n, label)` — N most recent emails in a label
- `get_email(message_id)` — full email content
- `search_emails(query)` — Gmail search syntax

**Core pattern (Gmail API):**
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

@mcp.tool()
async def list_recent_emails(n: int = 10, label: str = "INBOX") -> str:
    """List the N most recent emails. Returns sender, subject, snippet."""
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    service = build("gmail", "v1", credentials=creds)
    result = service.users().messages().list(
        userId="me", labelIds=[label], maxResults=n
    ).execute()
    # fetch metadata for each message...
```

---

## Recipe 8: Web scraper / reader

**What it does:** Fetch web pages, strip HTML to readable text, extract structured data.

**Tools:**
- `fetch_page(url)` — fetch and clean a web page
- `extract_links(url)` — get all links from a page
- `fetch_json(url, headers)` — fetch a JSON endpoint

**Core pattern:**
```python
import httpx
from bs4 import BeautifulSoup

@mcp.tool()
async def fetch_page(url: str) -> str:
    """Fetch a web page and return its text content, stripped of HTML."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        response = await client.get(url, headers={"User-Agent": "mcp-reader/1.0"})
        response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    # Truncate if too long
    return text[:8000] if len(text) > 8000 else text
```

---

## Recipe 9: Code execution sandbox

**What it does:** Run Python code snippets safely and return output. Useful for Claude to verify calculations or test code.

**Tools:**
- `run_python(code, timeout)` — run code in a subprocess
- `run_shell(command, cwd)` — run a shell command

**Core pattern:**
```python
import subprocess
import tempfile

@mcp.tool()
async def run_python(code: str, timeout: int = 10) -> str:
    """Run a Python code snippet. Returns stdout and stderr."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        tmppath = f.name
    result = subprocess.run(
        ["python3", tmppath],
        capture_output=True, text=True, timeout=timeout
    )
    return json.dumps({
        "stdout": result.stdout[:4000],
        "stderr": result.stderr[:2000],
        "returncode": result.returncode,
    })
```

Security note: code execution sandboxes require careful isolation. Consider running in a Docker container or using a service like E2B for production use.

---

## Recipe 10: Calendar and task manager

**What it does:** Read and write calendar events and tasks. Connects to Google Calendar or a local database.

**Tools:**
- `list_events(date_from, date_to)` — events in a date range
- `create_event(title, start, end, description)` — create a new event
- `list_tasks(list_name)` — pending tasks
- `complete_task(task_id)` — mark a task done

**Core pattern (local SQLite):**
```python
@mcp.tool()
async def create_event(title: str, start: str, end: str, description: str = "") -> str:
    """
    Create a calendar event.
    start and end must be ISO 8601 datetime strings, e.g. '2026-04-01T14:00:00'.
    """
    from datetime import datetime
    # Validate datetime strings
    datetime.fromisoformat(start)
    datetime.fromisoformat(end)
    event_id = str(uuid.uuid4())
    DB.execute(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?)",
        (event_id, title, start, end, description)
    )
    DB.commit()
    return f"Created event '{title}' from {start} to {end} (id: {event_id})"
```

---

Each recipe here is a starting point. The working examples in `examples/` demonstrate the full implementation for the first three.
