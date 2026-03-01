"""Shared fixtures for HD MCP tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from hd_mcp.config import Config, reset_config


# ---------------------------------------------------------------------------
# Config fixture
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_config():
    """Ensure config singleton is cleared between tests."""
    reset_config()
    yield
    reset_config()


@pytest.fixture
def mock_config() -> Config:
    return Config(
        hd_api_key="test-hd-key",
        hd_api_base_url="https://productapi.homedepot.com",
        hd_default_store_id=None,
        anthropic_api_key="test-anthropic-key",
        claude_model="claude-sonnet-4-6",
        hd_request_timeout=30.0,
    )


# ---------------------------------------------------------------------------
# Sample API response fixtures
# ---------------------------------------------------------------------------

SAMPLE_PRODUCT = {
    "itemId": "100672337",
    "productLabel": "DEWALT 20V MAX Cordless Drill",
    "brandName": "DEWALT",
    "nowPrice": 149.00,
    "averageRating": 4.8,
    "totalReviews": 1523,
    "productUrl": "https://www.homedepot.com/p/100672337",
    "media": {"images": [{"url": "https://images.homedepot-static.com/product.jpg"}]},
    "longDescription": "20V MAX cordless drill with 2-speed transmission.",
    "modelId": "DCD771C2",
    "availabilityType": {"type": "Online"},
    "pricing": {"nowPrice": 149.00, "wasPrice": 179.00},
    "specificationGroup": [],
}

SAMPLE_SEARCH_RESPONSE = {
    "searchReport": {"totalProducts": 42},
    "products": [SAMPLE_PRODUCT],
}

SAMPLE_STORE = {
    "storeId": 123,
    "storeName": "Home Depot - Austin North",
    "address": {
        "street": "7900 N Lamar Blvd",
        "city": "Austin",
        "state": "TX",
        "postalCode": "78753",
    },
    "phone": "512-555-1234",
    "storeHours": "Mon-Sat 6am-10pm, Sun 8am-8pm",
    "distance": 2.4,
}

SAMPLE_STORE_RESPONSE = {"storesDetails": [SAMPLE_STORE]}

SAMPLE_INVENTORY_RESPONSE = {
    "localInventory": {
        "inventory": [
            {"available": True, "quantity": 12, "aisle": "Building Materials", "bay": "5"}
        ]
    }
}


# ---------------------------------------------------------------------------
# Client mocks
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_hd_client() -> AsyncMock:
    client = AsyncMock()
    client.search_products.return_value = SAMPLE_SEARCH_RESPONSE
    client.get_product.return_value = SAMPLE_PRODUCT
    client.find_store.return_value = SAMPLE_STORE_RESPONSE
    client.check_inventory.return_value = SAMPLE_INVENTORY_RESPONSE
    return client


@pytest.fixture
def mock_anthropic_client() -> MagicMock:
    """AsyncAnthropic mock with pre-wired messages.create."""
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock()
    return client
