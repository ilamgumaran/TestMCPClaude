"""Async httpx client for the Home Depot Product API."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from hd_mcp.config import Config

logger = logging.getLogger(__name__)


class HomeDepotClient:
    """Async HTTP client for the Home Depot Product API.

    Use as an async context manager::

        async with HomeDepotClient(config) as client:
            results = await client.search_products(keyword="drill")
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> HomeDepotClient:
        self._client = httpx.AsyncClient(
            base_url=self._config.hd_api_base_url,
            headers={"X-HD-apikey": self._config.hd_api_key},
            timeout=self._config.hd_request_timeout,
        )
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError(
                "HomeDepotClient must be used as an async context manager."
            )
        return self._client

    async def _get(self, path: str, params: dict[str, Any]) -> Any:
        # Remove None values so they're not sent as query params
        clean_params = {k: v for k, v in params.items() if v is not None}
        t0 = time.monotonic()
        logger.debug("HD API GET %s params=%s", path, clean_params)
        response = await self._http.get(path, params=clean_params)
        elapsed = time.monotonic() - t0
        logger.debug("HD API %s → %d (%.3fs)", path, response.status_code, elapsed)
        response.raise_for_status()
        return response.json()

    async def search_products(
        self,
        keyword: str,
        page_size: int = 10,
        start_index: int = 0,
        store_id: str | None = None,
        sort_by: str | None = None,
    ) -> dict[str, Any]:
        """Search products by keyword.

        GET /products/v2/search
        """
        return await self._get(
            "/products/v2/search",
            {
                "keyword": keyword,
                "pageSize": page_size,
                "startIndex": start_index,
                "storeId": store_id,
                "sortby": sort_by,
            },
        )

    async def get_product(
        self,
        item_id: str,
        store_id: str | None = None,
    ) -> dict[str, Any]:
        """Get full product detail by item ID.

        GET /products/v2/products/{itemId}
        """
        return await self._get(
            f"/products/v2/products/{item_id}",
            {"storeId": store_id},
        )

    async def check_inventory(
        self,
        item_id: str,
        store_id: str,
    ) -> dict[str, Any]:
        """Check in-store inventory for an item.

        GET /localInventory/v2/inventory
        """
        return await self._get(
            "/localInventory/v2/inventory",
            {"itemId": item_id, "storeId": store_id},
        )

    async def find_store(
        self,
        zip_code: str,
        radius: int = 25,
    ) -> dict[str, Any]:
        """Find stores near a ZIP code.

        GET /store/v2/storeDetails
        """
        return await self._get(
            "/store/v2/storeDetails",
            {"zipCode": zip_code, "radius": radius},
        )
