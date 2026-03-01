# MCP Tools Specification

## Overview

The Home Depot MCP server exposes a set of tools that allow an AI assistant (or any
MCP client) to search, filter, and retrieve product information from Home Depot to
assist users with home improvement projects.

---

## Tools

### 1. `search_products`

Search Home Depot's catalog by keyword, category, or project context.

**Input Schema**

| Parameter      | Type     | Required | Description                                              |
|----------------|----------|----------|----------------------------------------------------------|
| `query`        | string   | yes      | Search term (e.g. "PVC pipe 1/2 inch", "drywall screws") |
| `category`     | string   | no       | Department/category filter (e.g. "Plumbing", "Electrical") |
| `page_size`    | integer  | no       | Number of results to return (default: 10, max: 24)       |
| `page`         | integer  | no       | Page number for pagination (default: 1)                  |
| `store_id`     | string   | no       | Filter by store availability                            |
| `sort_by`      | string   | no       | `relevance` \| `price_asc` \| `price_desc` \| `top_rated` |

**Output**

```json
{
  "total_results": 142,
  "page": 1,
  "products": [
    {
      "item_id": "202038841",
      "name": "1/2 in. x 10 ft. PVC Schedule 40 Pipe",
      "brand": "Charlotte Pipe",
      "price": 3.48,
      "rating": 4.7,
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

| Parameter   | Type   | Required | Description                    |
|-------------|--------|----------|--------------------------------|
| `item_id`   | string | yes      | Home Depot product item ID     |
| `store_id`  | string | no       | Include local inventory if set |

**Output**

Full product record including: description, specifications, dimensions, model number,
brand, price, availability (online + in-store), images, and related products.

---

### 3. `get_project_products`

Given a project description, return a curated list of relevant products.
Uses semantic understanding of the project to suggest materials and tools.

**Input Schema**

| Parameter       | Type     | Required | Description                                           |
|-----------------|----------|----------|-------------------------------------------------------|
| `project`       | string   | yes      | Free-text project description (e.g. "build a deck")  |
| `store_id`      | string   | no       | Prefer in-stock items at this store                  |
| `budget`        | number   | no       | Rough budget in USD to guide product tier selection  |
| `detail_level`  | string   | no       | `summary` \| `detailed` (default: `summary`)         |

**Output**

Categorized product list with reasoning — e.g. lumber, fasteners, tools, finishes —
with search queries used and top candidates per category.

---

### 4. `check_inventory`

Check in-store or online availability for a product.

**Input Schema**

| Parameter   | Type   | Required | Description                           |
|-------------|--------|----------|---------------------------------------|
| `item_id`   | string | yes      | Home Depot product item ID            |
| `store_id`  | string | yes      | Store ID to check local inventory     |
| `zip_code`  | string | no       | Zip code to find nearest store        |

**Output**

```json
{
  "item_id": "202038841",
  "store_id": "6902",
  "in_stock": true,
  "quantity": 47,
  "aisle": "25",
  "bay": "003",
  "online_stock": "In Stock",
  "ship_to_store_available": true
}
```

---

### 5. `find_store`

Find Home Depot store locations near a zip code.

**Input Schema**

| Parameter  | Type    | Required | Description                                  |
|------------|---------|----------|----------------------------------------------|
| `zip_code` | string  | yes      | ZIP code to search near                      |
| `radius`   | integer | no       | Search radius in miles (default: 25, max: 100)|
| `limit`    | integer | no       | Max stores to return (default: 5)            |

**Output**

List of stores with store ID, name, address, phone, hours, and distance.

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

| Code                  | Meaning                                   |
|-----------------------|-------------------------------------------|
| `PRODUCT_NOT_FOUND`   | Item ID does not exist                    |
| `STORE_NOT_FOUND`     | Store ID invalid or not found             |
| `API_ERROR`           | Upstream Home Depot API failure           |
| `RATE_LIMITED`        | API rate limit exceeded                   |
| `INVALID_PARAMS`      | Missing or invalid input parameters       |
