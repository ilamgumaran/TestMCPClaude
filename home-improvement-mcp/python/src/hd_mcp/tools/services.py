"""Handler for the find_services MCP tool.

Home Depot offers professional installation and repair services
(plumbing, electrical, flooring, appliance install, etc.).
These are surfaced via the product search API under a services category.
"""

from __future__ import annotations

from typing import Any

import httpx

from hd_mcp.client import HomeDepotClient


def _map_service(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a raw HD API service product to the services output schema."""
    return {
        "item_id": raw.get("itemId", ""),
        "name": raw.get("productLabel", ""),
        "provider": raw.get("brandName", ""),
        "price": raw.get("nowPrice"),
        "price_note": "Price shown is a starting estimate; final cost varies by scope.",
        "rating": raw.get("averageRating"),
        "review_count": raw.get("totalReviews"),
        "url": raw.get("productUrl", ""),
        "description": raw.get("longDescription", raw.get("description", "")),
    }


async def handle_find_services(
    client: HomeDepotClient,
    service_type: str,
    zip_code: str | None = None,
    store_id: str | None = None,
    project_description: str | None = None,
) -> dict[str, Any]:
    """Find Home Depot professional installation or repair services.

    Home Depot offers pro services (plumbing, electrical, flooring install,
    appliance installation, etc.) bookable through the store.
    Results are scoped to the customer's nearest store when zip_code is provided.

    Args:
        service_type: Type of service needed
                      (e.g. "plumber", "electrician", "flooring installation",
                      "appliance installation", "toilet installation",
                      "water heater installation")
        zip_code: Customer ZIP code to find services available at nearest store
        store_id: Store ID (used instead of zip_code if already known)
        project_description: Optional context to refine the search query
                             (e.g. "replacing a 40-gallon gas water heater")
    """
    if not service_type or not service_type.strip():
        return {
            "error": True,
            "code": "INVALID_PARAMS",
            "message": "service_type must be a non-empty string.",
        }

    if not zip_code and not store_id:
        return {
            "error": True,
            "code": "INVALID_PARAMS",
            "message": "Either zip_code or store_id must be provided to find local services.",
        }

    # Resolve store_id from zip_code if needed
    resolved_store_id = store_id
    if not resolved_store_id and zip_code:
        try:
            store_data = await client.find_store(zip_code=zip_code.strip(), radius=25)
            stores = store_data.get("storesDetails", [])
            if not stores:
                return {
                    "error": True,
                    "code": "STORE_NOT_FOUND",
                    "message": f"No Home Depot stores found near ZIP code '{zip_code}'.",
                }
            resolved_store_id = str(stores[0].get("storeId", ""))
        except httpx.HTTPStatusError as exc:
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

    # Build search keyword: service type + optional project context
    keyword = service_type.strip()
    if project_description:
        keyword = f"{keyword} {project_description.strip()}"

    try:
        data = await client.search_products(
            keyword=keyword,
            page_size=5,
            start_index=0,
            store_id=resolved_store_id,
            sort_by="bestseller",
        )
    except httpx.HTTPStatusError as exc:
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

    products_raw = data.get("products", [])
    report = data.get("searchReport", {})

    return {
        "service_type": service_type.strip(),
        "store_id": resolved_store_id,
        "zip_code": zip_code,
        "total": report.get("totalProducts", len(products_raw)),
        "services": [_map_service(p) for p in products_raw],
    }
