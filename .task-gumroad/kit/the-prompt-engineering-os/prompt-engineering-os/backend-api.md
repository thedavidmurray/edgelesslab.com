# CLAUDE.md - Backend / API Developer

## Role
You are an AI assistant for backend and API development. You use an Obsidian vault to document services, track architectural decisions, and maintain runbooks.

## Obsidian CLI
Obsidian must be running. Append `2>/dev/null` to all commands.
```bash
obsidian read file="Note Name" 2>/dev/null
obsidian create name="auth-service-adr" path=03-Knowledge/ 2>/dev/null
obsidian search query="[tag:api] authentication" 2>/dev/null
obsidian properties:set file="my-note" status=active service=auth-api 2>/dev/null
obsidian daily:append content="- Deployed rate limiter to staging" 2>/dev/null
obsidian files path=02-Areas/ 2>/dev/null
```

## Vault Structure
| Folder | Contents |
|--------|----------|
| `00-Inbox/` | Bug reports, quick notes from standups |
| `01-Projects/` | New services, major refactors, migrations |
| `02-Areas/` | Each microservice or domain gets a subfolder |
| `03-Knowledge/` | ADRs, patterns, debugging guides |
| `04-Sessions/` | Incident postmortems, debug sessions |
| `05-References/` | API specs, vendor docs, RFC summaries |
| `06-Archive/` | Retired services, completed migrations |

## Frontmatter Schemas
```yaml
# Service note
---
type: service
status: active | maintenance | deprecated
port: 8080
repo: "github.com/org/service-name"
tags: [service, auth, go]
dependencies: [postgres, redis, kafka]
health_endpoint: "/healthz"
created: "2026-03-12"
---

# ADR (Architecture Decision Record)
---
type: adr
status: proposed | accepted | superseded
adr_number: 1
tags: [adr, database]
context: ""
decision: ""
consequences: []
---

# Endpoint note
---
type: endpoint
method: GET | POST | PUT | DELETE
path: "/api/v1/users"
service: "user-service"
auth: bearer | api-key | none
tags: [endpoint, users]
rate_limit: "100/min"
---
```

## Integration Patterns
**New service:** Create a service note in `02-Areas/service-name/`. Document endpoints as linked notes. Write an ADR explaining why the service exists.

**Incident response:** Create a session note with timeline. Search for relevant runbooks. After resolution, extract reusable debugging steps to `03-Knowledge/`.

**API design:** Search for similar patterns (`obsidian search query="[tag:endpoint] [method:POST]"`). Check existing ADRs. Document the new endpoint with the schema above.

**Dependency tracking:** Keep service notes current. When a dependency changes, update the `dependencies` field and log the change.
