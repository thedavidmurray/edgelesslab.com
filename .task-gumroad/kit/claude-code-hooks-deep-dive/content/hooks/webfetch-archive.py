#!/usr/bin/env python3
"""
webfetch-archive.py - PostToolUse hook for WebFetch/mcp__fetch__fetch
Archives fetched web content to Obsidian vault for persistent reference.

Saves to: claude-vault/00-Inbox/web-fetches/YYYY-MM-DD-<slug>.md
With YAML frontmatter: url, domain, fetched_at, title

Only fires for WebFetch and mcp__fetch__fetch tool calls.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# Configuration
# Override with WEBFETCH_ARCHIVE_DIR env var or uses <project>/webfetch-archive by default
_default_archive = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).parent.parent.parent)) / "webfetch-archive"
VAULT_DIR = Path(os.environ.get("WEBFETCH_ARCHIVE_DIR", str(_default_archive)))
MAX_CONTENT_SIZE = 200_000  # 200KB max per file
TOOL_NAMES = {"WebFetch", "mcp__fetch__fetch", "webfetch", "fetch"}

# Ensure output directory exists
VAULT_DIR.mkdir(parents=True, exist_ok=True)


def slugify(text: str, max_len: int = 60) -> str:
    """Convert text to a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:max_len].rstrip('-')


def extract_title(content: str) -> str:
    """Try to extract a title from HTML or markdown content."""
    # HTML <title>
    m = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()[:120]
    # First markdown heading
    m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if m:
        return m.group(1).strip()[:120]
    return ""


def main():
    try:
        raw = sys.stdin.read(500_000)
        hook_input = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({"continue": True}))
        return

    # Claude Code PostToolUse sends: tool, input, output (or tool_name, tool_input, etc.)
    tool_name = hook_input.get("tool", hook_input.get("tool_name", ""))

    # Only process web fetch tools
    if tool_name not in TOOL_NAMES:
        print(json.dumps({"continue": True}))
        return

    # Extract URL and content
    tool_input = hook_input.get("input", hook_input.get("tool_input", {}))
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            tool_input = {}

    url = tool_input.get("url", tool_input.get("uri", ""))
    if not url:
        print(json.dumps({"continue": True}))
        return

    # Get the fetched content from tool output
    tool_output = hook_input.get("output", hook_input.get("result", hook_input.get("tool_output", "")))
    if isinstance(tool_output, dict):
        content = tool_output.get("content", tool_output.get("text", json.dumps(tool_output)))
    elif isinstance(tool_output, list):
        # MCP fetch returns array of content blocks
        parts = []
        for block in tool_output:
            if isinstance(block, dict):
                parts.append(block.get("text", block.get("content", str(block))))
            else:
                parts.append(str(block))
        content = "\n".join(parts)
    else:
        content = str(tool_output) if tool_output else ""

    if not content or len(content) < 50:
        print(json.dumps({"continue": True}))
        return

    # Parse URL for metadata
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")

    # Extract or generate title
    title = extract_title(content)
    if not title:
        # Use URL path as fallback title
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        title = path_parts[-1] if path_parts else domain

    # Clean title for display
    title_clean = re.sub(r'<[^>]+>', '', title)  # Strip any HTML tags
    title_clean = re.sub(r'\s+', ' ', title_clean).strip()

    # Build filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(title_clean or domain)
    filename = f"{date_str}-{slug}.md"
    filepath = VAULT_DIR / filename

    # Avoid overwriting — append counter if exists
    counter = 1
    while filepath.exists():
        filename = f"{date_str}-{slug}-{counter}.md"
        filepath = VAULT_DIR / filename
        counter += 1

    # Truncate content if too large
    if len(content) > MAX_CONTENT_SIZE:
        content = content[:MAX_CONTENT_SIZE] + "\n\n---\n*[Content truncated at 200KB]*\n"

    # Build markdown note
    note = f"""---
url: {url}
domain: {domain}
title: "{title_clean}"
fetched_at: {datetime.now().isoformat()}
type: web-fetch
tags:
  - web-fetch
  - {domain.split('.')[0]}
---

# {title_clean}

**Source**: [{domain}]({url})
**Fetched**: {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

{content}
"""

    try:
        filepath.write_text(note, encoding="utf-8")
    except Exception:
        pass  # Don't fail the hook on write error

    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
