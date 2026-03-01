# Use Cases

## Actors

| Actor         | Description                                                         |
|---------------|---------------------------------------------------------------------|
| MCP Client    | Any MCP-compatible client (Claude Desktop, Claude Code, custom app) |
| User          | The person interacting with the MCP client                         |
| HD API        | Home Depot Product API (external system)                           |
| Claude Model  | `claude-sonnet-4-6` (used in project recommendation flow)          |

---

## UC-01: Search Products by Keyword

**Actor**: MCP Client
**Trigger**: User asks for a specific product type (e.g. "show me 2x4 lumber options")
**Precondition**: Server is running; `HD_API_KEY` is set

**Main Flow**:
1. Client invokes `search_products` with a `query` string
2. Server calls HD API `/products/v2/search` with the query
3. HD API returns a list of matching products
4. Server formats and returns paginated results to the client

**Alternate Flow — No Results**:
- HD API returns 0 results → Server returns empty list with `total_results: 0`

**Alternate Flow — API Error**:
- HD API returns 5xx → Server returns `{ error: true, code: "API_ERROR" }`

---

## UC-02: Get Full Product Details

**Actor**: MCP Client
**Trigger**: User wants more detail on a specific product
**Precondition**: User has a valid Home Depot item ID (e.g. from a prior search)

**Main Flow**:
1. Client invokes `get_product` with an `item_id`
2. Server calls HD API `/products/v2/products/{itemId}`
3. HD API returns full product record
4. Server returns structured detail including specs, dimensions, model number, price

**Alternate Flow — Item Not Found**:
- HD API returns 404 → Server returns `{ error: true, code: "PRODUCT_NOT_FOUND" }`

---

## UC-03: Get Product Recommendations for a Project

**Actor**: MCP Client
**Trigger**: User describes a project (e.g. "I'm building a 12x16 deck")
**Precondition**: `HD_API_KEY` and `ANTHROPIC_API_KEY` are set

**Main Flow**:
1. Client invokes `get_project_products` with a `project` description
2. Server calls `claude-sonnet-4-6` to decompose the project into categories + queries
3. Server runs `search_products` for each category (in parallel)
4. Server calls `claude-sonnet-4-6` again to rank and curate results
5. Server returns a categorized product list to the client

**Alternate Flow — Model Unavailable**:
- Anthropic API call fails → Server returns `{ error: true, code: "API_ERROR" }` with
  message indicating model inference failed

**Alternate Flow — Budget Provided**:
- If `budget` param is set, model is instructed to prefer products within budget tier

---

## UC-04: Check In-Store Inventory

**Actor**: MCP Client
**Trigger**: User asks "is this in stock at my local store?"
**Precondition**: User has item ID and store ID (or zip code to resolve store)

**Main Flow**:
1. Client invokes `check_inventory` with `item_id` and `store_id`
2. Server calls HD API `/localInventory/v2/inventory`
3. HD API returns stock level and location (aisle/bay)
4. Server returns availability data to client

**Alternate Flow — Zip Code Provided**:
- If `zip_code` is provided instead of `store_id`:
  1. Server calls `find_store` to resolve nearest store
  2. Uses returned store ID for inventory check

---

## UC-05: Find Nearby Stores

**Actor**: MCP Client
**Trigger**: User asks "what Home Depot stores are near me?"
**Precondition**: User provides a ZIP code

**Main Flow**:
1. Client invokes `find_store` with a `zip_code`
2. Server calls HD API `/store/v2/storeDetails`
3. Server returns list of stores with name, address, hours, distance

**Alternate Flow — No Stores in Radius**:
- HD API returns empty list → Server returns empty array with informational message

---

## UC-06: Paginated Product Browse

**Actor**: MCP Client
**Trigger**: User wants to see more results beyond the first page
**Precondition**: Prior `search_products` call was made

**Main Flow**:
1. Client invokes `search_products` with same query and `page: 2` (or higher)
2. Server forwards pagination params to HD API
3. HD API returns next page of results
4. Server returns results with `page` and `total_results` for client-side navigation

---

## UC-07: Filtered Search by Category and Sort

**Actor**: MCP Client
**Trigger**: User wants lumber sorted by price, within a specific department
**Precondition**: None beyond running server

**Main Flow**:
1. Client invokes `search_products` with `query`, `category`, and `sort_by`
2. Server applies filters and sort to HD API call
3. Filtered, sorted results returned to client
