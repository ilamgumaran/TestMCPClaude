"""Handler for the get_product MCP tool."""

from __future__ import annotations

from typing import Any

import httpx

from hd_mcp.client import HomeDepotClient


def _map_product_detail(raw: dict[str, Any]) -> dict[str, Any]:
    """Map raw HD API product detail to the spec output schema."""
    pricing = raw.get("pricing", {})
    media = raw.get("media", {})
    images = media.get("images", []) if media else []

    return {
        "item_id": raw.get("itemId", ""),
        "name": raw.get("productLabel", ""),
        "brand": raw.get("brandName", ""),
        "description": raw.get("longDescription", raw.get("description", "")),
        "price": pricing.get("nowPrice") if pricing else raw.get("nowPrice"),
        "original_price": pricing.get("wasPrice") if pricing else raw.get("wasPrice"),
        "rating": raw.get("averageRating"),
        "review_count": raw.get("totalReviews"),
        "url": raw.get("productUrl", ""),
        "images": [img.get("url") for img in images if img.get("url")],
        "specifications": raw.get("specificationGroup", []),
        "model_number": raw.get("modelId", ""),
        "availability": raw.get("availabilityType", {}).get("type")
        if raw.get("availabilityType")
        else None,
    }


async def handle_get_product(
    client: HomeDepotClient,
    item_id: str,
    store_id: str | None = None,
) -> dict[str, Any]:
    """Get full product detail by item ID."""
    if not item_id or not item_id.strip():
        return {
            "error": True,
            "code": "INVALID_PARAMS",
            "message": "item_id must be a non-empty string.",
        }

    try:
        data = await client.get_product(item_id=item_id.strip(), store_id=store_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return {
                "error": True,
                "code": "PRODUCT_NOT_FOUND",
                "message": f"Product '{item_id}' not found.",
            }
        return {
            "error": True,
            "code": "API_ERROR",
            "message": f"Home Depot API error: {exc.response.status_code}",
        }
    except httpx.RequestError as exc:
        return {
            "error": True,
            "code": "API_ERROR",
            "message": f"Network error contacting Home Depot API: {exc}",
        }

    return _map_product_detail(data)
