# Home Improvement MCP Server

An MCP server that connects to the Home Depot Product API to help AI assistants
find relevant products for home improvement projects.

## Structure

```
home-improvement-mcp/
├── requirements/           # Functional + non-functional requirements, use cases
│   ├── requirements.md
│   └── use-cases.md
├── specs/                  # Speckit: features, scenarios, acceptance criteria
│   ├── features/           # Feature definitions (what and why)
│   ├── scenarios/          # BDD scenarios (given/when/then)
│   └── acceptance/         # Acceptance criteria checklists
├── python/                 # Python implementation (to be created)
└── golang/                 # Go implementation (to be created)
```

## Foundational Docs

See `../docs/` for workspace-level decisions:
- `tech-stack.md` — languages, SDKs, tooling
- `tools.md` — MCP tool definitions and schemas
- `model.md` — AI model configuration
- `architecture.md` — system architecture and data flows

## MCP Tools

| Tool                  | Description                                          |
|-----------------------|------------------------------------------------------|
| `search_products`     | Keyword search across HD product catalog             |
| `get_product`         | Full product details by item ID                      |
| `get_project_products`| AI-curated product list from a project description   |
| `check_inventory`     | In-store inventory by item ID and store              |
| `find_store`          | Nearest Home Depot stores by ZIP code                |

## Quick Start (coming after implementation)

```bash
# Python
cd python
HD_API_KEY=xxx ANTHROPIC_API_KEY=xxx uv run mcp dev server.py

# Go
cd golang
HD_API_KEY=xxx ANTHROPIC_API_KEY=xxx go run cmd/server/main.go
```
