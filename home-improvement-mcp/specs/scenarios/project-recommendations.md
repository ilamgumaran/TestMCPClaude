# Scenarios: Project-Based Product Recommendations

**Feature**: F-03

---

## Scenario S-03-01: Successful project decomposition and product retrieval

```
Given the MCP server is running
And HD_API_KEY and ANTHROPIC_API_KEY are set
When the client calls get_project_products with project "build a 12x16 pressure treated deck"
Then the response contains a list of product categories
And each category has a name and a list of products
And categories include at minimum: Lumber, Fasteners, Hardware
And each product has: item_id, name, price, url
```

---

## Scenario S-03-02: Project with budget constraint

```
Given the MCP server is running
And HD_API_KEY and ANTHROPIC_API_KEY are set
When the client calls get_project_products with project "paint a bedroom" and budget 150
Then the response products are generally priced below the budget threshold
And the model selects mid-range or economy product tiers
```

---

## Scenario S-03-03: Project with store preference

```
Given the MCP server is running
And HD_API_KEY and ANTHROPIC_API_KEY are set
And store_id "6902" has known inventory
When the client calls get_project_products with project "fix a leaky faucet" and store_id "6902"
Then the response preferentially includes products available at store 6902
```

---

## Scenario S-03-04: Missing project description

```
Given the MCP server is running
When the client calls get_project_products without a project parameter
Then the response contains error true
And the error code is "INVALID_PARAMS"
```

---

## Scenario S-03-05: Model API failure

```
Given the MCP server is running
And the Anthropic API is configured to return an error (test/mock scenario)
When the client calls get_project_products with project "tile a bathroom floor"
Then the response contains error true
And the error code is "API_ERROR"
And the error message mentions model inference failure
And the server does not crash
```

---

## Scenario S-03-06: Vague project description

```
Given the MCP server is running
And HD_API_KEY and ANTHROPIC_API_KEY are set
When the client calls get_project_products with project "fix stuff around the house"
Then the response still returns at least one category with products
And the model makes a reasonable interpretation (e.g. general repair supplies)
```
