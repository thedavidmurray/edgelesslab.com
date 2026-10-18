# 04 — Building Resources

Resources let Claude read content from your server without calling a tool. They are identified by URIs and can be static or dynamically generated.

## When to use resources vs tools

| Use a resource when | Use a tool when |
|--------------------|-----------------|
| The content exists and can be identified by a URI | You need to take an action or transform input |
| Claude needs to read something once and refer back to it | The result depends on parameters at call time |
| Content is large and better fetched on demand | You need side effects (write, send, delete) |
| You want Claude to be able to list available content | — |

Examples of resources: config files, database records, API documentation, log files, cached results.

## Static resources

A static resource has a fixed URI. The handler is called whenever Claude reads that URI.

**TypeScript:**
```typescript
server.resource(
  "App Config",
  "config://app/settings",
  { mimeType: "application/json" },
  async () => {
    const config = loadConfig();
    return {
      contents: [{
        uri: "config://app/settings",
        mimeType: "application/json",
        text: JSON.stringify(config, null, 2),
      }],
    };
  }
);
```

**Python (FastMCP):**
```python
@mcp.resource(
    uri="config://app/settings",
    name="App Config",
    description="Current application configuration",
    mime_type="application/json",
)
async def app_config() -> str:
    config = load_config()
    return json.dumps(config, indent=2)
```

## Resource templates (parameterized URIs)

Resource templates use RFC 6570 URI template syntax. Variables are enclosed in `{curly_braces}`.

```
file://{path}                    → file:///home/user/docs/README.md
db://records/{table}/{id}        → db://records/users/42
report://monthly/{year}/{month}  → report://monthly/2026/03
```

**TypeScript:**
```typescript
server.resource(
  "Database Record",
  "db://records/{table}/{id}",
  { mimeType: "application/json" },
  async (uri) => {
    const match = uri.href.match(/^db:\/\/records\/(\w+)\/(.+)$/);
    if (!match) throw new Error(`Invalid URI: ${uri.href}`);
    const [, table, id] = match;
    const record = await db.query(table, id);
    return {
      contents: [{
        uri: uri.href,
        mimeType: "application/json",
        text: JSON.stringify(record, null, 2),
      }],
    };
  }
);
```

**Python:**
```python
@mcp.resource(
    uri="db://records/{table}/{id}",
    name="Database Record",
    description="Fetch a record from the database by table and ID.",
    mime_type="application/json",
)
async def db_record(uri: str) -> str:
    match = re.match(r"^db://records/(\w+)/(.+)$", uri)
    if not match:
        raise ValueError(f"Invalid URI: {uri}")
    table, record_id = match.groups()
    record = await db.query(table, record_id)
    return json.dumps(record, indent=2)
```

## Content types

| MIME type | Use for |
|-----------|---------|
| `text/plain` | Raw text, logs |
| `application/json` | Structured data |
| `text/markdown` | Documentation, notes |
| `text/html` | Web content |
| `image/png`, `image/jpeg` | Images (return as base64 in `blob` field) |

For binary content, use the `blob` field instead of `text`:

```typescript
return {
  contents: [{
    uri: uri.href,
    mimeType: "image/png",
    blob: imageBuffer.toString("base64"),
  }],
};
```

## Resource lists

Claude calls `resources/list` to discover what resources are available. The SDK returns all statically registered resources. For dynamic lists (e.g., files in a directory), override the list handler:

**Python (low-level SDK):**
```python
@server.list_resources()
async def list_resources():
    files = list_data_files()
    return [
        Resource(
            uri=f"data://files/{f.name}",
            name=f.name,
            mimeType="text/csv",
        )
        for f in files
    ]
```

## URI scheme conventions

Use a custom URI scheme that identifies your server:

```
myapp://...
mycompany-myserver://...
```

Avoid using `file://` unless your resource genuinely maps to files. Generic schemes create ambiguity.

## Resource content guidelines

- Return content at an appropriate size. A resource returning 50MB of data will cause problems.
- If content is large, either paginate (via URI parameters) or summarize and offer a tool to fetch specific sections.
- Keep content stable across reads unless underlying data has changed. Volatile resources confuse Claude.
- Include a `Last-Modified` or timestamp field in structured resources so Claude knows how fresh the data is.

Next: [Building Prompts](05-building-prompts.md).
