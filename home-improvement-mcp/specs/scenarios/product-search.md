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
And total_from_api is greater than 0
And page is 1
And keyword_sent equals "pressure treated 2x4 8ft"
```

---

## Scenario S-01-02: Search with category filter

```
Given the MCP server is running
When the client calls search_products with query "deck screws" and category "Hardware"
Then keyword_sent starts with "Hardware"
And total_from_api is greater than 0
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
Then total_from_api equals 0
And total_after_filters equals 0
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

---

## Scenario S-01-08: Search with brand preference

```
Given the MCP server is running
When the client calls search_products with query "drill" and brand "DEWALT"
Then keyword_sent contains "DEWALT"
And the response contains filters.brand equal to "DEWALT"
And returned products are biased toward DEWALT items
```

---

## Scenario S-01-09: Search with product_types array

```
Given the MCP server is running
When the client calls search_products with:
  query "drill"
  product_types ["hammer drill", "SDS drill"]
Then keyword_sent contains "hammer drill"
And keyword_sent contains "SDS drill"
And keyword_sent contains "drill"
And the response contains filters.product_types equal to ["hammer drill", "SDS drill"]
```

---

## Scenario S-01-10: Search with features array

```
Given the MCP server is running
When the client calls search_products with:
  query "drill"
  features ["cordless", "brushless", "20V MAX"]
Then keyword_sent contains "cordless"
And keyword_sent contains "brushless"
And keyword_sent contains "20V MAX"
```

---

## Scenario S-01-11: Search with material and color

```
Given the MCP server is running
When the client calls search_products with:
  query "faucet"
  material "stainless steel"
  color "brushed nickel"
Then keyword_sent contains "stainless steel"
And keyword_sent contains "brushed nickel"
```

---

## Scenario S-01-12: Price filter excludes out-of-range products

```
Given the MCP server is running
When the client calls search_products with query "drill" and max_price 100.00
Then all products in the response have price <= 100.00
And total_after_filters may be less than total_from_api
And no products with price > 100.00 appear in the results
```

---

## Scenario S-01-13: Rating filter excludes low-rated products

```
Given the MCP server is running
When the client calls search_products with query "drill" and min_rating 4.5
Then all products in the response have rating >= 4.5
And products with rating < 4.5 are excluded from the results list
```

---

## Scenario S-01-14: ZIP code resolves to nearest store

```
Given the MCP server is running
When the client calls search_products with query "lumber" and zip_code "78753"
Then the server resolves the nearest store to zip 78753
And calls the HD API with the resolved store_id
And the response contains filters.zip_code equal to "78753"
```

---

## Scenario S-01-15: store_id takes precedence over zip_code

```
Given the MCP server is running
When the client calls search_products with:
  query "lumber"
  store_id "6902"
  zip_code "78753"
Then the server does NOT call find_store
And the HD API is called with store_id "6902"
```

---

## Scenario S-01-16: ZIP lookup failure is non-fatal

```
Given the MCP server is running
And find_store returns an error for the given ZIP code
When the client calls search_products with query "lumber" and zip_code "99999"
Then the search proceeds without a store filter
And the response does not contain an error
And products are returned (not store-filtered)
```

---

## Scenario S-01-17: Full attribute combination

```
Given the MCP server is running
When the client calls search_products with:
  query "drill"
  category "power tools"
  product_types ["hammer drill", "rotary hammer"]
  brand "DEWALT"
  features ["cordless", "brushless"]
  max_price 300.00
  sort_by "top_rated"
Then keyword_sent equals "power tools hammer drill rotary hammer drill cordless brushless DEWALT"
And all returned products have price <= 300.00
```
