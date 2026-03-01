# Requirements

## Project

**Name**: Home Improvement MCP Server
**Retailer**: Home Depot
**Purpose**: Provide an MCP-compliant server that enables AI assistants to search and
retrieve Home Depot product data relevant to a user's home improvement project.

---

## Functional Requirements

### FR-01 — Product Search
The server MUST allow clients to search Home Depot's product catalog using a keyword
or phrase. Results MUST include product name, brand, price, rating, and a direct URL.

### FR-02 — Product Detail Retrieval
The server MUST allow clients to retrieve full product details by Home Depot item ID,
including specifications, dimensions, model number, and availability.

### FR-03 — Project-Based Product Recommendations
The server MUST accept a free-text project description and return a categorized list
of relevant products sourced from Home Depot. The decomposition and curation MUST be
performed by `claude-sonnet-4-6`.

### FR-04 — Inventory Check
The server MUST allow clients to check in-store inventory for a product at a given
store, including aisle/bay location when available.

### FR-05 — Store Lookup
The server MUST allow clients to find Home Depot store locations near a ZIP code,
returning store ID, address, hours, and distance.

### FR-06 — Dual Implementation
The server MUST be implemented in both Python (3.12+) and Go (1.22+), with identical
tool interfaces and behavior.

---

## Non-Functional Requirements

### NFR-01 — MCP Compliance
Both implementations MUST conform to the Model Context Protocol specification.
They MUST support `stdio` transport and SHOULD support `SSE` transport.

### NFR-02 — Response Latency
- `search_products`, `get_product`, `check_inventory`, `find_store`: < 2s p95
- `get_project_products`: < 10s p95 (includes model inference + parallel searches)

### NFR-03 — Error Resilience
The server MUST return structured error responses (not crash) for all failure modes:
API errors, invalid input, rate limiting, and network timeouts.

### NFR-04 — Configuration via Environment
All secrets (API keys) and tunable settings MUST be read from environment variables.
No credentials may appear in source code or spec files.

### NFR-05 — Testability
Each tool MUST have unit tests covering happy path and key error cases.
Tests MUST be runnable without a live Home Depot API key (via mocking/fixtures).

### NFR-06 — Observability
The server MUST log each tool invocation with input parameters, upstream API call
results (status codes), and total elapsed time.

---

## Constraints

- Read-only access to Home Depot API (no cart/purchase functionality)
- Home Depot API rate limits must be respected; implement exponential backoff
- The `get_project_products` tool requires a valid `ANTHROPIC_API_KEY`
- Implementations must be independently deployable (no shared runtime dependency)
