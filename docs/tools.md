# MCP Tools Specification

## Overview

The Home Depot MCP server exposes 6 tools. The client (Claude in the UI) decides which
tools to call based on customer intent:

- **Simple product search** → call `search_products` directly (one call)
- **Project or problem shopping** → call `decompose_project` first, then call
  `search_products` or `find_services` once per step in the returned `shopping_plan`

Customer preferences (`brand`, `zip_code`) are forwarded on every relevant call.

---

## Tools

### 1. `search_products`

Search Home Depot's catalog. All structured attributes are combined into a single
keyword string sent to the API while also being returned in the response for transparency.

**Input Schema**

| Parameter       | Type       | Required | Description |
|-----------------|------------|----------|-------------|
| `query`         | string     | yes      | Core search term (e.g. `"drill"`, `"toilet flapper"`) |
| `product_types` | string[]   | no       | Specific product forms as an array — each joined into keyword. E.g. `["hammer drill", "SDS drill"]` |
| `category`      | string     | no       | Broad category context (e.g. `"power tools"`, `"plumbing"`) |
| `brand`         | string     | no       | Customer's preferred brand — appended to keyword (e.g. `"DEWALT"`, `"Moen"`) |
| `model`         | string     | no       | Specific model number or name (e.g. `"DCD771C2"`, `"Fluidmaster 400A"`) |
| `features`      | string[]   | no       | Feature keywords as array — each joined into keyword (e.g. `["cordless", "brushless", "20V MAX"]`) |
| `material`      | string     | no       | Material type (e.g. `"stainless steel"`, `"cedar"`, `"PVC"`) |
| `color`         | string     | no       | Color or finish (e.g. `"brushed nickel"`, `"oil rubbed bronze"`) |
| `min_price`     | number     | no       | Minimum price in USD — applied after API returns results |
| `max_price`     | number     | no       | Maximum price in USD — applied after API returns results |
| `min_rating`    | number     | no       | Minimum star rating 1–5 — applied after API returns results |
| `store_id`      | string     | no       | Filter by store availability (use if store already resolved) |
| `zip_code`      | string     | no       | Customer ZIP code — auto-resolved to nearest store (ignored if `store_id` set) |
| `page`          | integer    | no       | Page number, 1-based (default: 1) |
| `page_size`     | integer    | no       | Results per page (default: 10, max: 40) |
| `sort_by`       | string     | no       | `"bestseller"` \| `"top_rated"` \| `"price_asc"` \| `"price_desc"` |

**Keyword assembly order**

All structured inputs are combined into one keyword string:
```
[category] [product_types...] [query] [features...] [material] [color] [model] [brand]
```

**Output**

```json
{
  "query": "drill",
  "keyword_sent": "power tools hammer drill SDS drill drill cordless brushless DEWALT",
  "filters": {
    "category": "power tools",
    "product_types": ["hammer drill", "SDS drill"],
    "brand": "DEWALT",
    "model": null,
    "features": ["cordless", "brushless"],
    "material": null,
    "color": null,
    "min_price": null,
    "max_price": 300.0,
    "min_rating": null,
    "store_id": "6902",
    "zip_code": "78753"
  },
  "page": 1,
  "page_size": 10,
  "total_from_api": 142,
  "total_after_filters": 18,
  "products": [
    {
      "item_id": "202038841",
      "name": "DEWALT 20V MAX SDS Hammer Drill",
      "brand": "DEWALT",
      "price": 249.00,
      "rating": 4.8,
      "review_count": 1203,
      "url": "https://www.homedepot.com/p/...",
      "thumbnail": "https://images.thdstatic.com/..."
    }
  ]
}
```

---

### 2. `get_product`

Retrieve full details for a specific product by its Home Depot item ID.

**Input Schema**

| Parameter  | Type   | Required | Description                           |
|------------|--------|----------|---------------------------------------|
| `item_id`  | string | yes      | Home Depot product item ID            |
| `store_id` | string | no       | Include local pricing/inventory if set |

**Output**

Full product record including: name, brand, description, model number, price,
original price, availability, specifications, images list.

---

### 3. `decompose_project`

Break a home improvement project or problem into a step-by-step shopping plan.
Uses `claude-sonnet-4-6` to interpret the project and produce a list of products
and services needed. The client then calls `search_products` or `find_services`
once per step.

**When to use**: When the customer describes a project or problem to solve
(e.g. `"fix a broken toilet"`, `"rebuild kitchen cabinets"`, `"install ceiling fan"`).
Do NOT use for simple product questions — call `search_products` directly.

**Input Schema**

| Parameter  | Type   | Required | Description |
|------------|--------|----------|-------------|
| `project`  | string | yes      | Project or problem description |
| `zip_code` | string | no       | Customer ZIP — used to flag whether local services apply |
| `budget`   | number | no       | Total budget in USD |

**Output**

```json
{
  "project": "fix broken toilet",
  "zip_code": "78753",
  "budget": null,
  "project_summary": "Replace broken toilet components to restore function.",
  "difficulty": "diy",
  "shopping_plan": [
    {
      "step": 1,
      "type": "product",
      "category": "plumbing",
      "query": "toilet flapper replacement kit",
      "description": "Main repair component that controls water flow.",
      "tool_call": "search_products"
    },
    {
      "step": 2,
      "type": "product",
      "category": "tools",
      "query": "adjustable wrench plumbing",
      "description": "Needed to tighten supply line connections.",
      "tool_call": "search_products"
    },
    {
      "step": 3,
      "type": "service",
      "category": "plumber",
      "query": null,
      "description": "Professional plumber if DIY is too complex.",
      "tool_call": "find_services"
    }
  ],
  "notes": ["Turn off water supply valve before starting."],
  "estimated_items": 3
}
```

**Client follow-up contract**: For each item in `shopping_plan`:
- `tool_call == "search_products"` → call `search_products(query=item.query, zip_code=..., brand=...)`
- `tool_call == "find_services"` → call `find_services(service_type=item.category, zip_code=...)`

---

### 4. `find_services`

Find Home Depot professional installation or repair services available at the
customer's nearest store. Results are surfaced via the product search API
(HD lists installation services as bookable products).

**When to use**: For each `type="service"` step returned by `decompose_project`,
or when a customer asks directly about hiring a pro (e.g. `"can Home Depot install
my water heater?"`).

**Input Schema**

| Parameter             | Type   | Required | Description |
|-----------------------|--------|----------|-------------|
| `service_type`        | string | yes      | Type of service (e.g. `"plumber"`, `"electrician"`, `"flooring installation"`, `"water heater installation"`) |
| `zip_code`            | string | no*      | Customer ZIP — resolves to nearest store |
| `store_id`            | string | no*      | Store ID if already resolved |
| `project_description` | string | no       | Extra context to refine search (e.g. `"replacing 40-gallon gas water heater"`) |

\* Either `zip_code` or `store_id` is required.

**Output**

```json
{
  "service_type": "toilet installation",
  "store_id": "6902",
  "zip_code": "78753",
  "total": 4,
  "services": [
    {
      "item_id": "300123456",
      "name": "Toilet Installation Service",
      "provider": "Home Depot",
      "price": 119.00,
      "price_note": "Price shown is a starting estimate; final cost varies by scope.",
      "rating": 4.6,
      "review_count": 312,
      "url": "https://www.homedepot.com/s/...",
      "description": "Licensed plumber installs your toilet..."
    }
  ]
}
```

---

### 5. `check_inventory`

Check in-store availability for a product.

**Input Schema**

| Parameter  | Type   | Required | Description |
|------------|--------|----------|-------------|
| `item_id`  | string | yes      | Home Depot product item ID |
| `store_id` | string | no*      | Store to check inventory at |
| `zip_code` | string | no*      | Customer ZIP — auto-resolves to nearest store |

\* Either `store_id` or `zip_code` is required.

**Output**

```json
{
  "item_id": "202038841",
  "store_id": "6902",
  "inventory": [
    {
      "available": true,
      "quantity": 47,
      "aisle": "Building Materials",
      "bay": "5"
    }
  ]
}
```

---

### 6. `find_store`

Find Home Depot store locations near a ZIP code.

**Input Schema**

| Parameter  | Type    | Required | Description |
|------------|---------|----------|-------------|
| `zip_code` | string  | yes      | ZIP code to search near |
| `radius`   | integer | no       | Search radius in miles (default: 25, max: 100) |
| `limit`    | integer | no       | Max stores to return (default: 5) |

**Output**

List of stores with: `store_id`, `name`, `address` (street/city/state/zip),
`phone`, `hours`, `distance_miles`.

---

## Interaction Patterns

### Simple product search (1 call)
```
User: "best cordless DEWALT drill under $300"
→ search_products(query="drill", brand="DEWALT", features=["cordless"], max_price=300, sort_by="top_rated")
```

### Project shopping (N calls)
```
User: "I need to fix a broken toilet, I'm near ZIP 78753"
→ decompose_project(project="fix broken toilet", zip_code="78753")
   returns shopping_plan with 3 steps

→ search_products(query="toilet flapper replacement kit", zip_code="78753")
→ search_products(query="adjustable wrench plumbing", zip_code="78753")
→ find_services(service_type="plumber", zip_code="78753")
```

---

## Error Handling

All tools return structured errors:

```json
{
  "error": true,
  "code": "PRODUCT_NOT_FOUND",
  "message": "No product found with item_id 999999"
}
```

| Code                | Meaning |
|---------------------|---------|
| `PRODUCT_NOT_FOUND` | Item ID does not exist |
| `STORE_NOT_FOUND`   | Store ID invalid / no stores near ZIP |
| `API_ERROR`         | Upstream Home Depot or Anthropic API failure |
| `INVALID_PARAMS`    | Missing or invalid input parameters |
