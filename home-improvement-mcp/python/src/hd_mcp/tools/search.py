"""Handler for the search_products MCP tool."""

from __future__ import annotations

from typing import Any

import httpx

from hd_mcp.client import HomeDepotClient


def _map_product(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a raw HD API product dict to the spec output schema."""
    return {
        "item_id": raw.get("itemId", ""),
        "name": raw.get("productLabel", ""),
        "brand": raw.get("brandName", ""),
        "price": raw.get("nowPrice"),
        "rating": raw.get("averageRating"),
        "review_count": raw.get("totalReviews"),
        "url": raw.get("productUrl", ""),
        "thumbnail": raw.get("media", {}).get("images", [{}])[0].get("url")
        if raw.get("media")
        else None,
    }


def _build_keyword(
    query: str,
    category: str | None,
    product_types: list[str] | None,
    brand: str | None,
    model: str | None,
    features: list[str] | None,
    material: str | None,
    color: str | None,
) -> str:
    """Assemble all structured attributes into one HD-API keyword string.

    Order matters for relevance: broader context first, specifics last.
      [category] [product_types...] [query] [features...] [material] [color] [model] [brand]
    """
    parts: list[str] = []
    if category:
        parts.append(category.strip())
    if product_types:
        parts.extend(t.strip() for t in product_types if t.strip())
    parts.append(query.strip())
    if features:
        parts.extend(f.strip() for f in features if f.strip())
    if material:
        parts.append(material.strip())
    if color:
        parts.append(color.strip())
    if model:
        parts.append(model.strip())
    if brand:
        parts.append(brand.strip())
    return " ".join(parts)


async def handle_search_products(
    client: HomeDepotClient,
    query: str,
    # --- structured product attributes ---
    category: str | None = None,
    product_types: list[str] | None = None,
    brand: str | None = None,
    model: str | None = None,
    features: list[str] | None = None,
    material: str | None = None,
    color: str | None = None,
    # --- client-side result filters ---
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    # --- location ---
    store_id: str | None = None,
    zip_code: str | None = None,
    # --- pagination / sort ---
    page: int = 1,
    page_size: int = 10,
    sort_by: str | None = None,
) -> dict[str, Any]:
    """Search Home Depot products.

    All structured attributes (product_types, brand, model, features, material,
    color) are combined into a single keyword query sent to the API, while also
    being returned in the response so callers can see what was applied.
    """
    if not query or not query.strip():
        return {
            "error": True,
            "code": "INVALID_PARAMS",
            "message": "query must be a non-empty string.",
        }

    keyword = _build_keyword(
        query=query,
        category=category,
        product_types=product_types,
        brand=brand,
        model=model,
        features=features,
        material=material,
        color=color,
    )

    start_index = (page - 1) * page_size

    # Resolve store from zip_code when store_id not provided (non-fatal)
    resolved_store_id = store_id
    if not resolved_store_id and zip_code:
        try:
            store_data = await client.find_store(zip_code=zip_code.strip(), radius=25)
            stores = store_data.get("storesDetails", [])
            if stores:
                resolved_store_id = str(stores[0].get("storeId", ""))
        except (httpx.HTTPStatusError, httpx.RequestError):
            pass  # non-fatal; search proceeds without store filter

    try:
        data = await client.search_products(
            keyword=keyword,
            page_size=page_size,
            start_index=start_index,
            store_id=resolved_store_id,
            sort_by=sort_by,
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

    report = data.get("searchReport", {})
    products_raw = data.get("products", [])
    products = [_map_product(p) for p in products_raw]

    # Client-side filters (HD API has no native price/rating filter params)
    if min_price is not None:
        products = [p for p in products if p["price"] is not None and p["price"] >= min_price]
    if max_price is not None:
        products = [p for p in products if p["price"] is not None and p["price"] <= max_price]
    if min_rating is not None:
        products = [p for p in products if p["rating"] is not None and p["rating"] >= min_rating]

    return {
        # Echo back all inputs so Claude can include them in its response
        "query": query,
        "keyword_sent": keyword,
        "filters": {
            "category": category,
            "product_types": product_types,
            "brand": brand,
            "model": model,
            "features": features,
            "material": material,
            "color": color,
            "min_price": min_price,
            "max_price": max_price,
            "min_rating": min_rating,
            "store_id": resolved_store_id,
            "zip_code": zip_code,
        },
        "page": page,
        "page_size": page_size,
        "total_from_api": report.get("totalProducts", len(products_raw)),
        "total_after_filters": len(products),
        "products": products,
    }
