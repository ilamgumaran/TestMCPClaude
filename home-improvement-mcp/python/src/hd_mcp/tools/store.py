"""Handler for the find_store MCP tool."""

from __future__ import annotations

from typing import Any

import httpx

from hd_mcp.client import HomeDepotClient


def _map_store(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a raw HD API store dict to the spec output schema."""
    address = raw.get("address", {}) or {}
    return {
        "store_id": str(raw.get("storeId", "")),
        "name": raw.get("storeName", ""),
        "address": {
            "street": address.get("street", ""),
            "city": address.get("city", ""),
            "state": address.get("state", ""),
            "zip": address.get("postalCode", ""),
        },
        "phone": raw.get("phone", ""),
        "hours": raw.get("storeHours", ""),
        "distance_miles": raw.get("distance"),
    }


async def handle_find_store(
    client: HomeDepotClient,
    zip_code: str,
    radius: int = 25,
    limit: int = 5,
) -> dict[str, Any]:
    """Find Home Depot stores near a ZIP code."""
    if not zip_code or not zip_code.strip():
        return {
            "error": True,
            "code": "INVALID_PARAMS",
            "message": "zip_code must be a non-empty string.",
        }

    try:
        data = await client.find_store(zip_code=zip_code.strip(), radius=radius)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return {
                "error": True,
                "code": "STORE_NOT_FOUND",
                "message": f"No stores found near ZIP code '{zip_code}'.",
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

    stores_raw = data.get("storesDetails", [])
    stores = [_map_store(s) for s in stores_raw[:limit]]

    return {
        "zip_code": zip_code.strip(),
        "radius_miles": radius,
        "stores": stores,
    }
