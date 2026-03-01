# Tech Stack

## Overview

This project provides two parallel implementations of the Home Depot MCP server —
one in Python and one in Go — sharing the same specs, requirements, and acceptance
criteria.

---

## Languages & Runtimes

| Implementation | Language   | Version    |
|----------------|------------|------------|
| Primary        | Python     | 3.12+      |
| Secondary      | Go         | 1.22+      |

---

## MCP SDK

| Implementation | Library                    | Notes                                  |
|----------------|----------------------------|----------------------------------------|
| Python         | `mcp[cli]`                 | Official Anthropic MCP Python SDK      |
| Go             | `github.com/mark3labs/mcp-go` | Community Go MCP SDK, actively maintained |

---

## HTTP / API Client

| Implementation | Library       | Notes                          |
|----------------|---------------|--------------------------------|
| Python         | `httpx`       | Async-capable, modern requests |
| Go             | `net/http`    | Standard library               |

---

## Home Depot Integration

- **API**: Home Depot Product API (`productapi.homedepot.com`)
- **Auth**: API key header (`X-HD-apikey`)
- **Protocol**: REST / JSON
- **Key endpoints**:
  - `GET /products/v2/search` — keyword search with filters
  - `GET /products/v2/products/{itemId}` — product detail
  - `GET /products/v2/products/{itemId}/media` — images & media
  - `GET /store/v2/storeDetails` — store lookup
  - `GET /localInventory/v2/inventory` — in-store inventory

---

## Package Management

| Implementation | Tool    |
|----------------|---------|
| Python         | `uv`    |
| Go             | Go modules (`go mod`) |

---

## Testing

| Implementation | Framework          |
|----------------|--------------------|
| Python         | `pytest` + `pytest-asyncio` |
| Go             | `testing` (stdlib) + `testify` |

---

## Linting / Formatting

| Implementation | Tool                    |
|----------------|-------------------------|
| Python         | `ruff` (lint + format)  |
| Go             | `gofmt` / `golangci-lint` |

---

## Environment & Config

- Environment variables via `.env` (Python: `python-dotenv`, Go: `godotenv`)
- Required vars:
  - `HD_API_KEY` — Home Depot API key
  - `HD_API_BASE_URL` — default `https://productapi.homedepot.com`
  - `HD_DEFAULT_STORE_ID` — optional, for local inventory queries
