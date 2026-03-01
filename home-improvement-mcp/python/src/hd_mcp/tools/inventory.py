"""Handler for the check_inventory MCP tool."""

from __future__ import annotations

from typing import Any

import httpx

from hd_mcp.client import HomeDepotClient


async def handle_check_inventory(
    client: HomeDepotClient,
    item_id: str,
    store_id: str | None = None,
    zip_code: str | None = None,
) -> dict[str, Any]:
    """Check in-store inventory for a product.

    Requires either store_id or zip_code. If only zip_code is given, the
    nearest store is resolved first.
    """
    if not item_id or not item_id.strip():
        return {
            "error": True,
            "code": "INVALID_PARAMS",
            "message": "item_id must be a non-empty string.",
        }

    if not store_id and not zip_code:
        return {
            "error": True,
            "code": "INVALID_PARAMS",
            "message": "Either store_id or zip_code must be provided.",
        }

    # Resolve store_id from zip_code if needed
    resolved_store_id = store_id
    if not resolved_store_id and zip_code:
        try:
            store_data = await client.find_store(zip_code=zip_code, radius=25)
            stores = store_data.get("storesDetails", [])
            if not stores:
                return {
                    "error": True,
                    "code": "STORE_NOT_FOUND",
                    "message": f"No stores found near ZIP code '{zip_code}'.",
                }
            resolved_store_id = str(stores[0].get("storeId", ""))
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
                "message": f"Home Depot API error looking up store: {exc.response.status_code}",
            }
        except httpx.RequestError as exc:
            return {
                "error": True,
                "code": "API_ERROR",
                "message": f"Network error looking up store: {exc}",
            }

    try:
        data = await client.check_inventory(
            item_id=item_id.strip(),
            store_id=resolved_store_id,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return {
                "error": True,
                "code": "STORE_NOT_FOUND",
                "message": f"Store '{resolved_store_id}' not found or item not carried.",
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

    inv = data.get("localInventory", {})
    inventory_items = inv.get("inventory", []) if inv else []

    return {
        "item_id": item_id.strip(),
        "store_id": resolved_store_id,
        "inventory": [
            {
                "available": item.get("available", False),
                "quantity": item.get("quantity"),
                "aisle": item.get("aisle"),
                "bay": item.get("bay"),
            }
            for item in inventory_items
        ],
    }
