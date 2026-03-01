# Acceptance Criteria

All criteria apply to BOTH Python and Go implementations unless noted.

---

## AC-01: MCP Protocol Compliance

- [ ] Server starts and responds to MCP `initialize` handshake
- [ ] Server correctly lists all 5 tools in `tools/list` response
- [ ] Each tool's input schema matches the definition in `docs/tools.md`
- [ ] Server handles `stdio` transport
- [ ] Server handles `SSE` transport

---

## AC-02: Product Search (`search_products`)

- [ ] Returns results for a valid keyword query (S-01-01)
- [ ] Applies category filter correctly (S-01-02)
- [ ] Results sorted correctly when `sort_by` is specified (S-01-03)
- [ ] Returns empty list (not error) for no-results query (S-01-04)
- [ ] Pagination parameters forwarded correctly (S-01-05)
- [ ] Returns `INVALID_PARAMS` error when `query` is missing (S-01-06)
- [ ] Returns `API_ERROR` without crashing on HD API 5xx (S-01-07)
- [ ] All products in response include: `item_id`, `name`, `brand`, `price`, `rating`, `url`

---

## AC-03: Product Detail (`get_product`)

- [ ] Returns full product record for valid `item_id`
- [ ] Includes: name, brand, model number, price, dimensions, specifications, images
- [ ] Returns `PRODUCT_NOT_FOUND` for unknown item ID
- [ ] Returns `API_ERROR` without crashing on HD API failure
- [ ] When `store_id` is provided, includes inventory data in response

---

## AC-04: Project Recommendations (`get_project_products`)

- [ ] Returns categorized product list for a clear project description (S-03-01)
- [ ] Produces results in < 10 seconds p95 (NFR-02)
- [ ] Categories are reasonable for the described project
- [ ] Each product includes: `item_id`, `name`, `price`, `url`
- [ ] Budget parameter influences product tier selection (S-03-02)
- [ ] Store preference influences product selection (S-03-03)
- [ ] Returns `INVALID_PARAMS` when `project` is missing (S-03-04)
- [ ] Returns `API_ERROR` (not crash) when Anthropic API fails (S-03-05)
- [ ] Produces at least one category for vague project descriptions (S-03-06)

---

## AC-05: Inventory Check (`check_inventory`)

- [ ] Returns stock status and quantity for valid item + store (S-04-01)
- [ ] Returns `in_stock: false, quantity: 0` for OOS items (S-04-02)
- [ ] Resolves store from zip code when `store_id` omitted (S-04-03)
- [ ] Returns `STORE_NOT_FOUND` for invalid store ID (S-04-04)
- [ ] Returns aisle and bay when product is in stock

---

## AC-06: Store Lookup (`find_store`)

- [ ] Returns stores ordered by distance for a valid ZIP (S-05-01)
- [ ] Each store includes: `store_id`, `name`, `address`, `phone`, `hours`, `distance_miles`
- [ ] Returns empty list (not error) when no stores in radius (S-05-02)
- [ ] Returns `INVALID_PARAMS` when `zip_code` is missing (S-05-03)

---

## AC-07: Non-Functional

- [ ] All secrets read from environment variables (NFR-04)
- [ ] Each tool logs: invocation, upstream status code, elapsed time (NFR-06)
- [ ] All tools have unit tests runnable without live API keys (NFR-05)
- [ ] Search and detail tools respond in < 2s p95 (NFR-02)
- [ ] Server does not crash on any tested error scenario (NFR-03)

---

## Definition of Done

A tool is considered done when:
1. All acceptance criteria for that tool are checked
2. Unit tests pass in both Python and Go implementations
3. The tool has been manually tested against the live HD API
4. Scenarios in `specs/scenarios/` for that tool all pass
