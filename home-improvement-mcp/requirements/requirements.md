# Requirements

## Project

**Name**: Home Improvement MCP Server
**Retailer**: Home Depot
**Purpose**: Provide an MCP-compliant server that enables AI assistants to search and
retrieve Home Depot product and service data relevant to a user's home improvement need —
whether a simple product lookup or a full project shopping plan.

---

## Functional Requirements

### FR-01 — Product Search with Structured Attributes
The server MUST allow clients to search Home Depot's product catalog using a combination
of structured attributes. Results MUST include product name, brand, price, rating, and
a direct URL.

Supported attributes (all optional except `query`):
- `query` (required) — core search term
- `product_types` — array of product type names; each entry becomes part of the keyword
- `category` — broad department/category context
- `brand` — preferred brand, appended to keyword
- `model` — specific model number or name
- `features` — array of feature keywords; each entry becomes part of the keyword
- `material` — material type
- `color` — color or finish preference
- `min_price`, `max_price` — price range filter applied client-side after API returns
- `min_rating` — minimum star rating filter applied client-side after API returns
- `store_id` — filter by store availability
- `zip_code` — auto-resolved to nearest store when `store_id` is not provided

The server MUST echo back `keyword_sent` (the assembled keyword string) and
`total_after_filters` (count after client-side filtering) in the response.

### FR-02 — Product Detail Retrieval
The server MUST allow clients to retrieve full product details by Home Depot item ID,
including specifications, dimensions, model number, and availability.

### FR-03 — Project Decomposition
The server MUST accept a free-text project or problem description and return a
step-by-step shopping plan listing every product and professional service the customer
will need. Decomposition MUST be performed by `claude-sonnet-4-6`.

Each item in the plan MUST include:
- `type`: `"product"` or `"service"`
- `category`: short category name
- `query`: search term for products (omitted for services)
- `tool_call`: the tool the client should invoke for this step
  (`"search_products"` or `"find_services"`)

The client (Claude in the UI) is responsible for making one tool call per step.
The server does NOT perform the searches internally.

### FR-04 — Professional Services Discovery
The server MUST allow clients to find Home Depot professional installation and repair
services (e.g. plumbing, electrical, flooring installation, appliance installation)
available at the customer's nearest store. Results are resolved by `zip_code` or
`store_id`.

### FR-05 — Inventory Check
The server MUST allow clients to check in-store inventory for a product at a given
store, including aisle/bay location when available. The server MUST auto-resolve
`store_id` from `zip_code` when `store_id` is not provided.

### FR-06 — Store Lookup
The server MUST allow clients to find Home Depot store locations near a ZIP code,
returning store ID, address, hours, and distance.

### FR-07 — Dual Implementation
The server MUST be implemented in both Python (3.12+) and Go (1.22+), with identical
tool interfaces and behavior.

---

## Non-Functional Requirements

### NFR-01 — MCP Compliance
Both implementations MUST conform to the Model Context Protocol specification.
They MUST support `stdio` transport and SHOULD support `SSE` transport.

### NFR-02 — Response Latency
- `search_products`, `get_product`, `check_inventory`, `find_store`, `find_services`: < 2s p95
- `decompose_project`: < 5s p95 (one model inference call; no upstream product searches)

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
- The `decompose_project` tool requires a valid `ANTHROPIC_API_KEY`
- Implementations must be independently deployable (no shared runtime dependency)
- Client-side price and rating filters are applied in-process after the HD API returns;
  `total_after_filters` may be lower than `total_from_api`
