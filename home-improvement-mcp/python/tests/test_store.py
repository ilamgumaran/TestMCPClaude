"""Tests for handle_find_store."""

from __future__ import annotations

import httpx
import pytest

from hd_mcp.tools.store import handle_find_store


async def test_happy_path(mock_hd_client):
    result = await handle_find_store(mock_hd_client, zip_code="78753")

    assert result["zip_code"] == "78753"
    assert result["radius_miles"] == 25
    assert len(result["stores"]) == 1
    store = result["stores"][0]
    assert store["store_id"] == "123"
    assert store["name"] == "Home Depot - Austin North"
    assert store["address"]["city"] == "Austin"
    assert store["address"]["state"] == "TX"
    assert store["phone"] == "512-555-1234"
    assert store["distance_miles"] == 2.4

    mock_hd_client.find_store.assert_awaited_once_with(zip_code="78753", radius=25)


async def test_custom_radius_and_limit(mock_hd_client):
    # Provide 3 stores in response, limit=2
    from tests.conftest import SAMPLE_STORE
    mock_hd_client.find_store.return_value = {
        "storesDetails": [SAMPLE_STORE, SAMPLE_STORE, SAMPLE_STORE]
    }

    result = await handle_find_store(mock_hd_client, zip_code="78753", radius=50, limit=2)

    assert result["radius_miles"] == 50
    assert len(result["stores"]) == 2
    mock_hd_client.find_store.assert_awaited_once_with(zip_code="78753", radius=50)


async def test_empty_zip_returns_invalid_params(mock_hd_client):
    result = await handle_find_store(mock_hd_client, zip_code="")

    assert result["error"] is True
    assert result["code"] == "INVALID_PARAMS"
    mock_hd_client.find_store.assert_not_awaited()


async def test_no_stores_found(mock_hd_client):
    mock_hd_client.find_store.return_value = {"storesDetails": []}

    result = await handle_find_store(mock_hd_client, zip_code="00000")

    assert result["stores"] == []


async def test_404_returns_store_not_found(mock_hd_client):
    response = httpx.Response(404, request=httpx.Request("GET", "http://x"))
    mock_hd_client.find_store.side_effect = httpx.HTTPStatusError(
        "not found", request=response.request, response=response
    )

    result = await handle_find_store(mock_hd_client, zip_code="00000")

    assert result["error"] is True
    assert result["code"] == "STORE_NOT_FOUND"


async def test_5xx_returns_api_error(mock_hd_client):
    response = httpx.Response(503, request=httpx.Request("GET", "http://x"))
    mock_hd_client.find_store.side_effect = httpx.HTTPStatusError(
        "service unavailable", request=response.request, response=response
    )

    result = await handle_find_store(mock_hd_client, zip_code="78753")

    assert result["error"] is True
    assert result["code"] == "API_ERROR"
    assert "503" in result["message"]


async def test_network_error_returns_api_error(mock_hd_client):
    mock_hd_client.find_store.side_effect = httpx.ConnectError("no route")

    result = await handle_find_store(mock_hd_client, zip_code="78753")

    assert result["error"] is True
    assert result["code"] == "API_ERROR"


async def test_zip_stripped(mock_hd_client):
    await handle_find_store(mock_hd_client, zip_code="  78753  ")

    call_kwargs = mock_hd_client.find_store.call_args.kwargs
    assert call_kwargs["zip_code"] == "78753"
