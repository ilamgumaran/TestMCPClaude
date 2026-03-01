# Acceptance Criteria

All criteria apply to BOTH Python and Go implementations unless noted.

---

## AC-01: MCP Protocol Compliance

- [ ] Server starts and responds to MCP `initialize` handshake
- [ ] Server correctly lists all 6 tools in `tools/list` response:
      `search_products`, `get_product`, `decompose_project`, `find_services`,
      `check_inventory`, `find_store`
- [ ] Each tool's input schema matches the definition in `docs/tools.md`
- [ ] Server handles `stdio` transport
- [ ] Server handles `SSE` transport

---

## AC-02: Product Search (`search_products`)

- [ ] Returns results for a valid keyword query (S-01-01)
- [ ] Applies category filter — prepends to keyword (S-01-02)
- [ ] Results sorted correctly when `sort_by` is specified (S-01-03)
- [ ] Returns empty list (not error) for no-results query (S-01-04)
- [ ] Pagination parameters forwarded correctly (S-01-05)
- [ ] Returns `INVALID_PARAMS` error when `query` is missing (S-01-06)
- [ ] Returns `API_ERROR` without crashing on HD API 5xx (S-01-07)
- [ ] `brand` appended to keyword; echoed in `filters.brand` (S-01-08)
- [ ] `product_types` array: each entry included as separate words in keyword (S-01-09)
- [ ] `features` array: each entry included as separate words in keyword (S-01-10)
- [ ] `material` and `color` included in keyword (S-01-11)
- [ ] `max_price` filter excludes products above threshold; `total_after_filters` reflects count (S-01-12)
- [ ] `min_rating` filter excludes products below threshold (S-01-13)
- [ ] `zip_code` resolves to nearest store; `store_id` used in HD API call (S-01-14)
- [ ] `store_id` takes precedence over `zip_code`; no `find_store` call made (S-01-15)
- [ ] ZIP lookup failure is non-fatal; search proceeds without store filter (S-01-16)
- [ ] `keyword_sent` echoed in every successful response
- [ ] All products include: `item_id`, `name`, `brand`, `price`, `rating`, `url`

---

## AC-03: Product Detail (`get_product`)

- [ ] Returns full product record for valid `item_id`
- [ ] Includes: name, brand, model number, price, original price, description, images
- [ ] Returns `PRODUCT_NOT_FOUND` for unknown item ID
- [ ] Returns `API_ERROR` without crashing on HD API failure
- [ ] When `store_id` is provided, response includes local pricing context

---

## AC-04: Project Decomposition (`decompose_project`)

- [ ] Returns `shopping_plan` with at least 3 steps for a clear project description (S-03-01)
- [ ] Projects requiring professional work include `type: "service"` steps (S-03-02)
- [ ] Each step has: `step`, `type`, `category`, `description`, `tool_call` (S-03-01)
- [ ] Product steps have non-empty `query`; `tool_call` is `"search_products"` (S-03-01)
- [ ] Service steps have `tool_call` equal to `"find_services"` (S-03-02)
- [ ] `difficulty` field is one of `"diy"` | `"intermediate"` | `"professional"` (S-03-01)
- [ ] `budget` param is included in the Claude prompt when provided (S-03-04)
- [ ] `zip_code` returned in response when provided (S-03-05)
- [ ] Returns in < 5s p95 (NFR-02)
- [ ] Returns `INVALID_PARAMS` when `project` is empty (S-03-06)
- [ ] Returns `API_ERROR` (not crash) when Anthropic API fails (S-03-07)
- [ ] Returns at least one step for vague project descriptions (S-03-08)

---

## AC-05: Professional Services (`find_services`)

- [ ] Returns services list for valid `service_type` + `store_id` (S-03-09)
- [ ] Resolves store from `zip_code` when `store_id` not provided (S-03-09)
- [ ] `project_description` included in search keyword when provided (S-03-10)
- [ ] Returns `INVALID_PARAMS` when neither `store_id` nor `zip_code` provided (S-03-11)
- [ ] Returns `STORE_NOT_FOUND` when no stores found near ZIP (S-03-12)
- [ ] Returns `INVALID_PARAMS` when `service_type` is empty
- [ ] Each service includes: `item_id`, `name`, `provider`, `price`, `price_note`, `url`
- [ ] Returns `API_ERROR` without crashing on HD API failure

---

## AC-06: Inventory Check (`check_inventory`)

- [ ] Returns stock status and quantity for valid item + store (S-04-01)
- [ ] Returns inventory with `available: false` for OOS items (S-04-02)
- [ ] Resolves store from zip code when `store_id` omitted (S-04-03)
- [ ] Returns `STORE_NOT_FOUND` for invalid store ID (S-04-04)
- [ ] Returns `INVALID_PARAMS` when neither `store_id` nor `zip_code` provided
- [ ] Returns aisle and bay when product is in stock

---

## AC-07: Store Lookup (`find_store`)

- [ ] Returns stores ordered by distance for a valid ZIP (S-05-01)
- [ ] Each store includes: `store_id`, `name`, `address`, `phone`, `hours`, `distance_miles`
- [ ] Returns empty list (not error) when no stores in radius (S-05-02)
- [ ] Returns `INVALID_PARAMS` when `zip_code` is missing (S-05-03)

---

## AC-08: Non-Functional

- [ ] All secrets read from environment variables (NFR-04)
- [ ] Each tool logs: invocation, upstream status code, elapsed time (NFR-06)
- [ ] All tools have unit tests runnable without live API keys (NFR-05)
- [ ] `search_products`, `get_product`, `check_inventory`, `find_store`, `find_services`
      respond in < 2s p95 (NFR-02)
- [ ] `decompose_project` responds in < 5s p95 (NFR-02)
- [ ] Server does not crash on any tested error scenario (NFR-03)

---

## Definition of Done

A tool is considered done when:
1. All acceptance criteria for that tool are checked
2. Unit tests pass in both Python and Go implementations
3. The tool has been manually tested against the live HD API
4. Scenarios in `specs/scenarios/` for that tool all pass
