# Scenarios: Product Search

**Feature**: F-01

---

## Scenario S-01-01: Successful keyword search

```
Given the MCP server is running
And the HD_API_KEY environment variable is set
When the client calls search_products with query "pressure treated 2x4 8ft"
Then the response contains a list of products
And each product has fields: item_id, name, brand, price, rating, url
And total_results is greater than 0
And page is 1
```

---

## Scenario S-01-02: Search with category filter

```
Given the MCP server is running
When the client calls search_products with query "deck screws" and category "Hardware"
Then all returned products belong to the "Hardware" category
And total_results is greater than 0
```

---

## Scenario S-01-03: Search with sort by price ascending

```
Given the MCP server is running
When the client calls search_products with query "work gloves" and sort_by "price_asc"
Then products are ordered from lowest price to highest price
```

---

## Scenario S-01-04: Search with no results

```
Given the MCP server is running
When the client calls search_products with query "xyzzy_nonexistent_product_12345"
Then the response contains total_results equal to 0
And the products list is empty
And no error is returned
```

---

## Scenario S-01-05: Paginated search

```
Given the MCP server is running
When the client calls search_products with query "paint" and page 2 and page_size 10
Then the response contains page equal to 2
And the products list has at most 10 items
```

---

## Scenario S-01-06: Missing required parameter

```
Given the MCP server is running
When the client calls search_products without a query parameter
Then the response contains error true
And the error code is "INVALID_PARAMS"
```

---

## Scenario S-01-07: HD API failure

```
Given the MCP server is running
And the HD API is configured to return a 500 error (test/mock scenario)
When the client calls search_products with query "hammer"
Then the response contains error true
And the error code is "API_ERROR"
And the server does not crash
```
