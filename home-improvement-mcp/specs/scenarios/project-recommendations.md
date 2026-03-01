# Scenarios: Project Decomposition & Services

**Feature**: F-03 / F-04

---

## Scenario S-03-01: Successful project decomposition

```
Given the MCP server is running
And HD_API_KEY and ANTHROPIC_API_KEY are set
When the client calls decompose_project with project "build a 12x16 pressure treated deck"
Then the response contains a shopping_plan list
And shopping_plan has at least 3 steps
And at least one step has type "product" and category containing "lumber" or "fasteners"
And each step has: step, type, category, description, tool_call
And steps with type "product" have a non-empty query field
And steps with type "product" have tool_call equal to "search_products"
And steps with type "service" have tool_call equal to "find_services"
And the response contains difficulty
And the response contains notes (list)
```

---

## Scenario S-03-02: Project with required professional services

```
Given the MCP server is running
And HD_API_KEY and ANTHROPIC_API_KEY are set
When the client calls decompose_project with project "remodel kitchen with new electrical outlets"
Then at least one step has type "service"
And that step has tool_call equal to "find_services"
And that step has category containing "electrician" or "electrical"
And the difficulty is "intermediate" or "professional"
```

---

## Scenario S-03-03: Client makes one call per shopping_plan step

```
Given decompose_project returned a shopping_plan with N steps
When the client iterates over each step
Then for each step with tool_call "search_products":
  the client calls search_products with query equal to step.query
And for each step with tool_call "find_services":
  the client calls find_services with service_type equal to step.category
And the total number of downstream tool calls equals N
```

---

## Scenario S-03-04: Project with budget constraint

```
Given the MCP server is running
And HD_API_KEY and ANTHROPIC_API_KEY are set
When the client calls decompose_project with project "paint a bedroom" and budget 150
Then the budget value is included in the Claude prompt
And the response shopping_plan reflects budget-appropriate product queries
  (e.g. "economy interior paint" rather than "premium paint")
```

---

## Scenario S-03-05: Project with ZIP code

```
Given the MCP server is running
And HD_API_KEY and ANTHROPIC_API_KEY are set
When the client calls decompose_project with project "fix a leaky faucet" and zip_code "30301"
Then the response contains zip_code equal to "30301"
And the client forwards zip_code to each search_products and find_services call
```

---

## Scenario S-03-06: Missing project description

```
Given the MCP server is running
When the client calls decompose_project without a project parameter
Then the response contains error true
And the error code is "INVALID_PARAMS"
```

---

## Scenario S-03-07: Model API failure

```
Given the MCP server is running
And the Anthropic API is configured to return an error (test/mock scenario)
When the client calls decompose_project with project "tile a bathroom floor"
Then the response contains error true
And the error code is "API_ERROR"
And the server does not crash
And no shopping_plan is returned
```

---

## Scenario S-03-08: Vague project description

```
Given the MCP server is running
And HD_API_KEY and ANTHROPIC_API_KEY are set
When the client calls decompose_project with project "fix stuff around the house"
Then the response still returns a shopping_plan with at least one step
And the model makes a reasonable interpretation (e.g. general repair supplies)
```

---

## Scenario S-03-09: Successful find_services call

```
Given the MCP server is running
And HD_API_KEY is set
And a valid store_id or zip_code is provided
When the client calls find_services with service_type "toilet installation" and zip_code "78753"
Then the server resolves the nearest store from zip_code "78753"
And the response contains a services list
And each service has: item_id, name, provider, price, price_note, url
And the response contains store_id and zip_code
```

---

## Scenario S-03-10: find_services with project description context

```
Given the MCP server is running
When the client calls find_services with:
  service_type "water heater installation"
  store_id "6902"
  project_description "replacing 40-gallon gas water heater"
Then the HD API is called with a keyword containing "replacing 40-gallon gas water heater"
```

---

## Scenario S-03-11: find_services — no location provided

```
Given the MCP server is running
When the client calls find_services with service_type "plumber"
  but neither zip_code nor store_id is provided
Then the response contains error true
And the error code is "INVALID_PARAMS"
```

---

## Scenario S-03-12: find_services — no stores near ZIP

```
Given the MCP server is running
When the client calls find_services with service_type "electrician" and zip_code "00000"
And no Home Depot stores are found near that ZIP
Then the response contains error true
And the error code is "STORE_NOT_FOUND"
```
