"""FastMCP server — tool definitions and entrypoint.

## Interaction contract

Claude (in the client UI) decides which tools to call based on customer intent:

### Simple product search (one MCP call)
  Customer: "What is the best hammer drill?" or "Show me DEWALT drills near 78753"
  Claude calls: search_products(query="hammer drill", brand="DEWALT", zip_code="78753")

### Project / problem shopping (multiple MCP calls)
  Customer: "I need to fix a broken toilet" or "I'm rebuilding my kitchen"
  Step 1 — Claude calls: decompose_project(project="fix broken toilet", zip_code="78753")
  Step 2 — Claude reads shopping_plan from the response, then calls one tool per step:
    - For type="product" items → search_products(query=item["query"], zip_code=...)
    - For type="service" items → find_services(service_type=item["category"], zip_code=...)
  Step 3 — Claude presents consolidated results to customer

Customer preferences (brand, zip_code, store_id) are forwarded to every relevant call.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

import anthropic
from mcp.server.fastmcp import FastMCP

from hd_mcp.client import HomeDepotClient
from hd_mcp.config import get_config
from hd_mcp.tools import (
    handle_check_inventory,
    handle_decompose_project,
    handle_find_services,
    handle_find_store,
    handle_get_product,
    handle_search_products,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(server: Any):  # noqa: ANN001
    config = get_config()
    logger.info("Starting HD MCP server (model=%s)", config.claude_model)
    async with HomeDepotClient(config) as hd:
        yield {
            "hd": hd,
            "anthropic": anthropic.AsyncAnthropic(api_key=config.anthropic_api_key),
            "model": config.claude_model,
        }


mcp = FastMCP("hd-mcp", lifespan=lifespan)


def _lc() -> dict[str, Any]:
    ctx = mcp.get_context()
    return ctx.request_context.lifespan_context


# ---------------------------------------------------------------------------
# Tool: search_products
# Use when: customer wants a specific product or Claude is executing one step
# of a project shopping plan (type="product").
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_products(
    query: str,
    category: str | None = None,
    product_types: list[str] | None = None,
    brand: str | None = None,
    model: str | None = None,
    features: list[str] | None = None,
    material: str | None = None,
    color: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    store_id: str | None = None,
    zip_code: str | None = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: str | None = None,
) -> dict:
    """Search Home Depot products by keyword with structured attribute filters.

    Call this tool:
    - For a simple product request ("best hammer drill", "2x4 lumber")
    - For EACH product step returned by decompose_project (type="product" items)

    All structured attributes (product_types, brand, features, etc.) are combined
    into a single keyword sent to the API, so you get the benefits of structured
    input AND natural-language search. Pass every preference the customer mentions.

    Args:
        query: Core search term — what the customer is looking for
               (e.g. "drill", "toilet flapper", "deck screws")

        product_types: Specific product types as an array — each becomes part of
                       the search keyword. Use when the customer names multiple
                       acceptable product forms.
                       Example: ["hammer drill", "SDS drill", "rotary hammer"]
                       Example: ["flapper", "fill valve", "flush valve"]

        category: Broad product category to provide search context
                  (e.g. "power tools", "plumbing", "lumber", "paint")

        brand: Customer's preferred brand — appended to keyword to bias results
               (e.g. "DEWALT", "Milwaukee", "Moen", "Kohler", "Simpson Strong-Tie")

        model: Specific model number or name if customer knows it
               (e.g. "DCD771C2", "M18 FUEL", "Fluidmaster 400A")

        features: Product feature keywords as an array — each joined into keyword
                  (e.g. ["cordless", "brushless", "20V MAX"])
                  (e.g. ["pressure treated", "ground contact", "UC4B"])

        material: Material type (e.g. "stainless steel", "cedar", "PVC", "copper")

        color: Color or finish preference (e.g. "brushed nickel", "oil rubbed bronze")

        min_price: Minimum price in USD — filters results after API call
        max_price: Maximum price in USD — filters results after API call
        min_rating: Minimum star rating 1–5 — filters results after API call

        store_id: Filter by store availability (use if store_id already known)
        zip_code: Customer ZIP code — resolves to nearest store automatically;
                  ignored if store_id is provided

        page: Result page, 1-based (default 1)
        page_size: Results per page, max 40 (default 10)
        sort_by: "bestseller" | "top_rated" | "price_asc" | "price_desc"
    """
    lc = _lc()
    return await handle_search_products(
        client=lc["hd"],
        query=query,
        category=category,
        product_types=product_types,
        brand=brand,
        model=model,
        features=features,
        material=material,
        color=color,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        store_id=store_id,
        zip_code=zip_code,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
    )


# ---------------------------------------------------------------------------
# Tool: get_product
# Use when: customer asks for details on a specific item ID.
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_product(
    item_id: str,
    store_id: str | None = None,
) -> dict:
    """Get full product details by Home Depot item ID.

    Use when the customer references a specific product ID or when you need
    full specs/pricing after a search_products call.

    Args:
        item_id: Home Depot item ID (e.g. "100672337")
        store_id: Optional — include for local pricing and availability
    """
    lc = _lc()
    return await handle_get_product(
        client=lc["hd"],
        item_id=item_id,
        store_id=store_id,
    )


# ---------------------------------------------------------------------------
# Tool: decompose_project
# Use when: customer describes a project or problem to solve.
# Returns a shopping plan — then call search_products / find_services per step.
# ---------------------------------------------------------------------------

@mcp.tool()
async def decompose_project(
    project: str,
    zip_code: str | None = None,
    budget: float | None = None,
) -> dict:
    """Break a home improvement project into a step-by-step shopping plan.

    Use this tool when the customer describes a project or problem to solve
    (e.g. "fix a broken toilet", "build a deck", "install kitchen backsplash").
    Do NOT use this for simple product questions — use search_products directly.

    The response contains a shopping_plan list. For EACH item in the list:
    - If item["tool_call"] == "search_products" → call search_products with item["query"]
    - If item["tool_call"] == "find_services"   → call find_services with item["category"]

    Always forward customer preferences (zip_code, brand) to those follow-up calls.

    Args:
        project: Description of the project or problem
                 (e.g. "fix a broken toilet", "rebuild kitchen cabinets",
                 "install a ceiling fan", "refinish hardwood floors")
        zip_code: Customer ZIP code — used to flag whether local services apply
        budget: Optional total budget in USD
    """
    lc = _lc()
    return await handle_decompose_project(
        anthropic_client=lc["anthropic"],
        model=lc["model"],
        project=project,
        zip_code=zip_code,
        budget=budget,
    )


# ---------------------------------------------------------------------------
# Tool: find_services
# Use when: a decompose_project step has type="service", or customer asks
# about professional installation / repair.
# ---------------------------------------------------------------------------

@mcp.tool()
async def find_services(
    service_type: str,
    zip_code: str | None = None,
    store_id: str | None = None,
    project_description: str | None = None,
) -> dict:
    """Find Home Depot professional installation or repair services.

    Call this for EACH service step returned by decompose_project
    (type="service" items). Also use directly when a customer asks about
    hiring a pro (e.g. "can Home Depot install my water heater?").

    Home Depot offers bookable services including: appliance installation,
    flooring installation, water heater installation, cabinet installation,
    door/window installation, and more.

    Args:
        service_type: Type of service (e.g. "plumber", "electrician",
                      "flooring installation", "water heater installation",
                      "toilet installation", "appliance installation")
        zip_code: Customer ZIP code to find services at the nearest store
        store_id: Store ID (use instead of zip_code if already resolved)
        project_description: Optional extra context to refine results
                             (e.g. "replacing 40-gallon gas water heater")
    """
    lc = _lc()
    return await handle_find_services(
        client=lc["hd"],
        service_type=service_type,
        zip_code=zip_code,
        store_id=store_id,
        project_description=project_description,
    )


# ---------------------------------------------------------------------------
# Tool: check_inventory
# ---------------------------------------------------------------------------

@mcp.tool()
async def check_inventory(
    item_id: str,
    store_id: str | None = None,
    zip_code: str | None = None,
) -> dict:
    """Check in-store availability for a product.

    Use after search_products or get_product when the customer wants to
    know if an item is in stock at their local store.

    Requires either store_id or zip_code. If only zip_code is given,
    the nearest store is resolved automatically.

    Args:
        item_id: Home Depot item ID to check
        store_id: Store to check inventory at
        zip_code: Customer ZIP code (used if store_id not provided)
    """
    lc = _lc()
    return await handle_check_inventory(
        client=lc["hd"],
        item_id=item_id,
        store_id=store_id,
        zip_code=zip_code,
    )


# ---------------------------------------------------------------------------
# Tool: find_store
# ---------------------------------------------------------------------------

@mcp.tool()
async def find_store(
    zip_code: str,
    radius: int = 25,
    limit: int = 5,
) -> dict:
    """Find Home Depot stores near a ZIP code.

    Use when the customer asks where their nearest store is, or to resolve
    a store_id from a ZIP code before making inventory checks.

    Args:
        zip_code: US ZIP code to search from
        radius: Search radius in miles (default 25)
        limit: Max stores to return (default 5)
    """
    lc = _lc()
    return await handle_find_store(
        client=lc["hd"],
        zip_code=zip_code,
        radius=radius,
        limit=limit,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
