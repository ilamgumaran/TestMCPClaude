# Feature: Project Decomposition & Multi-Call Shopping

**ID**: F-03 / F-04
**Requirements**: FR-03, FR-04
**Use Cases**: UC-04, UC-05

## Summary

As an MCP client, I want to accept a free-text project or problem description, receive
a step-by-step shopping plan, and then execute one tool call per step — so that I can
guide the user through both product sourcing and professional service booking for any
home improvement project.

## Architecture

The server does NOT perform product searches internally for project flows. Instead:

1. **Client** calls `decompose_project` with the project description
2. **Server** calls `claude-sonnet-4-6` once to produce a `shopping_plan`
3. **Server** returns the plan immediately — no product searches happen server-side
4. **Client** iterates over `shopping_plan` and calls one MCP tool per step:
   - `type == "product"` → `search_products(query=step.query, zip_code=..., brand=...)`
   - `type == "service"` → `find_services(service_type=step.category, zip_code=...)`

This makes the client (Claude in the UI) the orchestrator, keeping each server call
fast and independently retryable.

## Scope: `decompose_project`

- Natural language project/problem description as input
- AI-driven step-by-step plan using `claude-sonnet-4-6`
- Each step tagged as `"product"` or `"service"` with an explicit `tool_call` field
- Products: specific HD-searchable keyword in `query`
- Services: professional labor / installation (plumbing, electrical, flooring, etc.)
- `difficulty` field: `"diy"` | `"intermediate"` | `"professional"`
- `notes` field: safety tips, permit requirements, sequencing advice
- Optional `budget` param passed to Claude to guide tier selection
- Optional `zip_code` used to flag whether local services are applicable

## Scope: `find_services`

- Searches HD catalog for bookable installation/repair services
- Scoped to the customer's nearest store (resolved from `zip_code` or `store_id`)
- Optional `project_description` refines the search keyword
- Returns: service name, provider, starting price, price disclaimer, rating, URL

## Out of Scope

- Server-side parallel search aggregation (client handles this)
- Bill-of-materials quantity estimation (future feature)
- Cost breakdown / project budgeting (future feature)
- Installation instructions or how-to guides
- Services outside the Home Depot catalog
