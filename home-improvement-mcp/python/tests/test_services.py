"""Tests for handle_find_services."""

from __future__ import annotations

import httpx
import pytest

from hd_mcp.tools.services import handle_find_services
from tests.conftest import SAMPLE_STORE_RESPONSE


async def test_happy_path_with_store_id(mock_hd_client):
    result = await handle_find_services(
        mock_hd_client,
        service_type="toilet installation",
        store_id="123",
    )

    assert result["service_type"] == "toilet installation"
    assert result["store_id"] == "123"
    assert "services" in result
    mock_hd_client.search_products.assert_awaited_once()
    # Should NOT call find_store when store_id already provided
    mock_hd_client.find_store.assert_not_awaited()


async def test_zip_code_resolves_store(mock_hd_client):
    result = await handle_find_services(
        mock_hd_client,
        service_type="plumber",
        zip_code="78753",
    )

    mock_hd_client.find_store.assert_awaited_once_with(zip_code="78753", radius=25)
    assert result["store_id"] == "123"
    assert result["zip_code"] == "78753"


async def test_project_description_appended_to_keyword(mock_hd_client):
    await handle_find_services(
        mock_hd_client,
        service_type="water heater installation",
        store_id="123",
        project_description="replacing 40-gallon gas water heater",
    )

    call_kwargs = mock_hd_client.search_products.call_args.kwargs
    assert "replacing 40-gallon gas water heater" in call_kwargs["keyword"]


async def test_empty_service_type_returns_invalid_params(mock_hd_client):
    result = await handle_find_services(mock_hd_client, service_type="", zip_code="78753")

    assert result["error"] is True
    assert result["code"] == "INVALID_PARAMS"
    mock_hd_client.search_products.assert_not_awaited()


async def test_no_location_returns_invalid_params(mock_hd_client):
    result = await handle_find_services(mock_hd_client, service_type="plumber")

    assert result["error"] is True
    assert result["code"] == "INVALID_PARAMS"


async def test_zip_no_stores_returns_store_not_found(mock_hd_client):
    mock_hd_client.find_store.return_value = {"storesDetails": []}

    result = await handle_find_services(
        mock_hd_client, service_type="plumber", zip_code="00000"
    )

    assert result["error"] is True
    assert result["code"] == "STORE_NOT_FOUND"


async def test_search_api_error_returns_api_error(mock_hd_client):
    response = httpx.Response(500, request=httpx.Request("GET", "http://x"))
    mock_hd_client.search_products.side_effect = httpx.HTTPStatusError(
        "error", request=response.request, response=response
    )

    result = await handle_find_services(
        mock_hd_client, service_type="electrician", store_id="123"
    )

    assert result["error"] is True
    assert result["code"] == "API_ERROR"


async def test_services_mapped_from_product_search(mock_hd_client):
    """Service results are mapped from the product search response."""
    result = await handle_find_services(
        mock_hd_client, service_type="flooring installation", store_id="123"
    )

    assert len(result["services"]) == 1
    svc = result["services"][0]
    assert svc["item_id"] == "100672337"
    assert "price_note" in svc  # pricing disclaimer always present
