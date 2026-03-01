# Use Cases

## Actors

| Actor        | Description |
|--------------|-------------|
| MCP Client   | Any MCP-compatible client (Claude Desktop, Claude Code, custom app) |
| User         | The person interacting with the MCP client |
| HD API       | Home Depot Product API (external system) |
| Claude Model | `claude-sonnet-4-6` — used in `decompose_project` to interpret projects |

---

## Intent Model

The MCP client determines how many tool calls to make based on the user's intent:

| User intent | Example | Client action |
|-------------|---------|---------------|
| **Simple product search** | "best hammer drill" | One call to `search_products` |
| **Product with preferences** | "DEWALT cordless drill near ZIP 78753 under $300" | One call to `search_products` with `brand`, `zip_code`, `max_price` |
| **Project / problem shopping** | "fix a broken toilet" | `decompose_project` → N calls to `search_products` + `find_services` |

---

## UC-01: Simple Product Search

**Actor**: MCP Client
**Trigger**: User asks for a specific product type (e.g. "show me 2x4 lumber options")
**Precondition**: Server is running; `HD_API_KEY` is set

**Main Flow**:
1. Client invokes `search_products` with a `query` string
2. Server assembles keyword and calls HD API `/products/v2/search`
3. HD API returns a list of matching products
4. Server formats and returns paginated results to the client

**Alternate Flow — No Results**:
- HD API returns 0 results → Server returns empty list with `total_from_api: 0`

**Alternate Flow — API Error**:
- HD API returns 5xx → Server returns `{ error: true, code: "API_ERROR" }`

---

## UC-02: Product Search with Customer Preferences

**Actor**: MCP Client
**Trigger**: User specifies preferences alongside a product request
  (e.g. "show me DEWALT cordless drills near ZIP 78753 under $200, at least 4.5 stars")
**Precondition**: Server is running; `HD_API_KEY` is set

**Main Flow**:
1. Client invokes `search_products` with `query`, `brand`, `zip_code`, `max_price`,
   `min_rating`, and any other relevant attributes
2. Server resolves nearest `store_id` from `zip_code`
3. Server assembles keyword from all structured attributes
   (e.g. `"drill cordless DEWALT"`)
4. Server calls HD API with assembled keyword and resolved `store_id`
5. Server applies `max_price` and `min_rating` filters to the returned results
6. Server returns filtered products with `keyword_sent` and `total_after_filters`

**Alternate Flow — Multiple Product Types**:
- User specifies `product_types: ["hammer drill", "SDS drill"]`
- Each type is included as separate words in the keyword: `"hammer drill SDS drill drill"`
- Results include matching products from all specified types

**Alternate Flow — ZIP Lookup Failure**:
- `find_store` returns no results or errors for the given ZIP
- Search proceeds without a store filter (non-fatal); results are not store-filtered

---

## UC-03: Get Full Product Details

**Actor**: MCP Client
**Trigger**: User wants more detail on a specific product
**Precondition**: User has a valid Home Depot item ID (e.g. from a prior search)

**Main Flow**:
1. Client invokes `get_product` with an `item_id`
2. Server calls HD API `/products/v2/products/{itemId}`
3. HD API returns full product record
4. Server returns structured detail including specs, dimensions, model number, price, images

**Alternate Flow — Item Not Found**:
- HD API returns 404 → Server returns `{ error: true, code: "PRODUCT_NOT_FOUND" }`

---

## UC-04: Project Shopping — Multi-Call Flow

**Actor**: MCP Client
**Trigger**: User describes a project or problem to solve
  (e.g. "I need to fix a broken toilet", "I'm rebuilding my kitchen")
**Precondition**: `HD_API_KEY` and `ANTHROPIC_API_KEY` are set

**Main Flow**:
1. Client invokes `decompose_project` with `project` (and optionally `zip_code`, `budget`)
2. Server calls `claude-sonnet-4-6` to decompose the project into a `shopping_plan`
3. Server returns the plan — a list of steps with `type`, `category`, `query`,
   `tool_call`, and `description`
4. Client reads `shopping_plan` and calls one tool per step:
   - For steps where `tool_call == "search_products"`: calls `search_products(query=step.query, zip_code=..., brand=...)`
   - For steps where `tool_call == "find_services"`: calls `find_services(service_type=step.category, zip_code=...)`
5. Client collects all results and presents consolidated recommendations to the user

**Alternate Flow — Project Requires Professional Services**:
- Claude includes steps with `type: "service"` for work requiring licensed tradespeople
  (electrical, plumbing rough-in, HVAC, structural)
- Client calls `find_services` for each service step
- Client presents both product and service options together

**Alternate Flow — Model Unavailable**:
- Anthropic API call fails → Server returns `{ error: true, code: "API_ERROR" }`
- Client surfaces the error; no follow-up tool calls made

**Alternate Flow — Budget Provided**:
- If `budget` param is set, Claude is instructed to prefer lower-cost product options
  and note whether the project is feasible within budget

---

## UC-05: Find Professional Services

**Actor**: MCP Client
**Trigger**: A `decompose_project` step has `tool_call == "find_services"`, OR user
  directly asks "can Home Depot install my water heater?"
**Precondition**: Customer ZIP code or store ID is known

**Main Flow**:
1. Client invokes `find_services` with `service_type` and `zip_code` (or `store_id`)
2. Server resolves nearest store from `zip_code` if `store_id` not provided
3. Server searches HD catalog for matching installation/service products at that store
4. Server returns list of available services with name, provider, starting price, and URL

**Alternate Flow — No Local Store**:
- No stores found near ZIP → `{ error: true, code: "STORE_NOT_FOUND" }`

---

## UC-06: Check In-Store Inventory

**Actor**: MCP Client
**Trigger**: User asks "is this in stock at my local store?"
**Precondition**: User has item ID and store ID (or zip code to resolve store)

**Main Flow**:
1. Client invokes `check_inventory` with `item_id` and `store_id`
2. Server calls HD API `/localInventory/v2/inventory`
3. HD API returns stock level and location (aisle/bay)
4. Server returns availability data to client

**Alternate Flow — ZIP Code Provided**:
- If `zip_code` provided instead of `store_id`:
  1. Server calls `find_store` to resolve nearest store
  2. Uses returned store ID for inventory check
  3. Response includes resolved `store_id`

---

## UC-07: Find Nearby Stores

**Actor**: MCP Client
**Trigger**: User asks "what Home Depot stores are near me?"
**Precondition**: User provides a ZIP code

**Main Flow**:
1. Client invokes `find_store` with a `zip_code`
2. Server calls HD API `/store/v2/storeDetails`
3. Server returns list of stores with name, address, hours, distance

**Alternate Flow — No Stores in Radius**:
- HD API returns empty list → Server returns empty `stores` array (not an error)

---

## UC-08: Paginated Product Browse

**Actor**: MCP Client
**Trigger**: User wants to see more results beyond the first page
**Precondition**: Prior `search_products` call was made

**Main Flow**:
1. Client invokes `search_products` with same query/attributes and `page: 2` (or higher)
2. Server forwards pagination params to HD API
3. Server returns next page with `page`, `total_from_api`, `total_after_filters`

---

## UC-09: Filtered Search by Attributes and Sort

**Actor**: MCP Client
**Trigger**: User specifies multiple attributes (e.g. "brushed nickel PVC fittings,
  sorted by price, max $50")
**Precondition**: None beyond running server

**Main Flow**:
1. Client invokes `search_products` with `query`, `material`, `color`, `max_price`,
   `sort_by`
2. Server assembles keyword from all provided attributes
3. Server applies sort via HD API; applies price filter client-side on returned results
4. Server returns `keyword_sent` so client can show what was searched
