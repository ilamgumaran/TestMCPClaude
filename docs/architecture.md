# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        MCP Client                           │
│          (Claude Desktop / Claude Code / custom app)        │
└──────────────────────────┬──────────────────────────────────┘
                           │  MCP Protocol (stdio / SSE)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Home Depot MCP Server                          │
│                                                             │
│  ┌──────────────┐   ┌──────────────────────────────────┐   │
│  │ Tool Router  │──▶│           Tool Handlers           │   │
│  └──────────────┘   │                                  │   │
│                     │  search_products                  │   │
│                     │  get_product                      │   │
│                     │  get_project_products  ──┐        │   │
│                     │  check_inventory         │        │   │
│                     │  find_store              │        │   │
│                     └──────────────────────────┼────────┘   │
│                                                │            │
│  ┌─────────────────────────────┐    ┌──────────▼──────────┐ │
│  │   Home Depot API Client     │    │  Anthropic Client   │ │
│  │   (httpx / net/http)        │    │  (claude-sonnet-4-6)│ │
│  └──────────────┬──────────────┘    └─────────────────────┘ │
└─────────────────┼───────────────────────────────────────────┘
                  │  HTTPS / REST
                  ▼
┌─────────────────────────────────────────────────────────────┐
│               Home Depot Product API                        │
│          productapi.homedepot.com                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Transport

The server supports two MCP transport modes:

| Mode    | Use case                                   |
|---------|--------------------------------------------|
| `stdio` | Claude Desktop / Claude Code integration  |
| `sse`   | HTTP-based clients, remote access          |

Default: `stdio`

---

## Dual Implementation Strategy

Both Python and Go implementations are **spec-identical** — they expose the same
tools, same input/output schemas, and same error codes. The specs in this repo
are the source of truth. Implementations must pass the same acceptance scenarios.

```
docs/                   ← foundational decisions (shared)
home-improvement-mcp/
  requirements/         ← what the system must do (shared)
  specs/                ← speckit feature + scenario specs (shared)
  python/               ← Python implementation
  golang/               ← Go implementation
```

---

## Data Flow: `get_project_products`

```
1. Client calls get_project_products(project="build a backyard deck")

2. Server sends project description to claude-sonnet-4-6:
   "Decompose this home improvement project into product categories
    and generate search queries for each."

3. Model returns structured categories:
   [
     { "category": "Lumber", "query": "pressure treated deck boards 5/4 x 6" },
     { "category": "Fasteners", "query": "deck screws composite 2.5 inch" },
     { "category": "Hardware", "query": "post anchor galvanized 4x4" },
     { "category": "Tools", "query": "circular saw 7.25 inch" }
   ]

4. Server calls search_products for each category in parallel.

5. Results are sent back to claude-sonnet-4-6 for ranking/curation.

6. Curated, categorized product list returned to client.
```

---

## Security Considerations

- API keys stored in environment variables only, never in code or specs
- Home Depot API key scoped to read-only product endpoints
- No user data persisted by the server
- Rate limiting: respect HD API limits (requests/minute configurable)
