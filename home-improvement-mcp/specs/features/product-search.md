# Feature: Product Search

**ID**: F-01
**Requirement**: FR-01
**Use Cases**: UC-01, UC-02, UC-08, UC-09

## Summary

As an MCP client, I want to search Home Depot's product catalog using structured
customer attributes so that I can surface the most relevant products for any product
request — simple keyword queries or preference-rich requests with brand, type,
features, material, and price constraints.

## Scope

- Keyword-based product search
- Structured attribute inputs: `product_types` (array), `category`, `brand`, `model`,
  `features` (array), `material`, `color`
- All structured attributes are combined into a single keyword string sent to the HD API
- `keyword_sent` echoed in response for transparency
- `zip_code` auto-resolved to nearest store; `store_id` used directly if provided
- Client-side result filtering: `min_price`, `max_price`, `min_rating`
- `total_from_api` (pre-filter count) and `total_after_filters` (post-filter count)
  both returned
- Sort order: `bestseller`, `top_rated`, `price_asc`, `price_desc`
- Pagination via `page` and `page_size`

## Keyword Assembly Order

```
[category] [product_types...] [query] [features...] [material] [color] [model] [brand]
```

Example — customer asks for a cordless DEWALT hammer drill or SDS drill, brushless:
```
product_types=["hammer drill", "SDS drill"]
brand="DEWALT"
features=["cordless", "brushless"]
query="drill"

→ keyword_sent: "hammer drill SDS drill drill cordless brushless DEWALT"
```

## Out of Scope

- Cart or purchase actions
- Price history or deal tracking
- Cross-retailer search
- Server-side price/rating filtering (HD API does not support these natively;
  filtering is applied in-process after results are returned)
