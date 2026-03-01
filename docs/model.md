# Model Configuration

## AI Model

| Setting       | Value                  |
|---------------|------------------------|
| Provider      | Anthropic              |
| Model ID      | `claude-sonnet-4-6`    |
| Family        | Claude 4.6             |
| Context       | 200k tokens            |

The model is used for **semantic project understanding** — specifically in the
`get_project_products` tool where a free-text project description must be
decomposed into product categories and search queries.

---

## When the Model Is Invoked

The MCP server itself does not always invoke the model. The model is invoked **only**
for the `get_project_products` tool, which requires:

1. Parsing the project description into actionable categories (e.g. framing, sheathing,
   fasteners, tools)
2. Generating precise search queries per category
3. Summarizing/ranking results against the project context

All other tools (`search_products`, `get_product`, `check_inventory`, `find_store`)
are pure API pass-throughs — no model inference needed.

---

## Invocation Pattern

```
User project description
        ↓
  claude-sonnet-4-6
  (decompose into categories + queries)
        ↓
  search_products (x N categories)
        ↓
  claude-sonnet-4-6
  (rank and curate results)
        ↓
  Structured product list returned to MCP client
```

---

## Anthropic SDK

| Implementation | Library               | Version  |
|----------------|-----------------------|----------|
| Python         | `anthropic`           | latest   |
| Go             | `github.com/anthropics/anthropic-sdk-go` | latest |

---

## Environment Variables

| Variable              | Description                                  |
|-----------------------|----------------------------------------------|
| `ANTHROPIC_API_KEY`   | Required for `get_project_products` tool     |
| `CLAUDE_MODEL`        | Override model ID (default: `claude-sonnet-4-6`) |

---

## Token Budget

For `get_project_products`:
- **Input**: project description + product results context
- **Max output tokens**: 1024 (structured JSON response)
- **Temperature**: 0.3 (focused, deterministic ranking)
