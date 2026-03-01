"""Tests for handle_check_inventory."""

from __future__ import annotations

import httpx
import pytest

from hd_mcp.tools.inventory import handle_check_inventory


async def test_happy_path_with_store_id(mock_hd_client):
    result = await handle_check_inventory(
        mock_hd_client, item_id="100672337", store_id="123"
    )

    assert result["item_id"] == "100672337"
    assert result["store_id"] == "123"
    assert len(result["inventory"]) == 1
    inv = result["inventory"][0]
    assert inv["available"] is True
    assert inv["quantity"] == 12
    assert inv["aisle"] == "Building Materials"
    assert inv["bay"] == "5"

    mock_hd_client.check_inventory.assert_awaited_once_with(
        item_id="100672337", store_id="123"
    )
    mock_hd_client.find_store.assert_not_awaited()


async def test_zip_code_resolves_store_id(mock_hd_client):
    result = await handle_check_inventory(
        mock_hd_client, item_id="100672337", zip_code="78753"
    )

    # Should have called find_store first
    mock_hd_client.find_store.assert_awaited_once_with(zip_code="78753", radius=25)
    # Then check_inventory with the resolved store id
    mock_hd_client.check_inventory.assert_awaited_once_with(
        item_id="100672337", store_id="123"
    )
    assert result["store_id"] == "123"


async def test_no_store_id_no_zip_returns_invalid_params(mock_hd_client):
    result = await handle_check_inventory(mock_hd_client, item_id="100672337")

    assert result["error"] is True
    assert result["code"] == "INVALID_PARAMS"
    mock_hd_client.check_inventory.assert_not_awaited()


async def test_empty_item_id_returns_invalid_params(mock_hd_client):
    result = await handle_check_inventory(
        mock_hd_client, item_id="", store_id="123"
    )

    assert result["error"] is True
    assert result["code"] == "INVALID_PARAMS"


async def test_zip_no_stores_returns_store_not_found(mock_hd_client):
    mock_hd_client.find_store.return_value = {"storesDetails": []}

    result = await handle_check_inventory(
        mock_hd_client, item_id="100672337", zip_code="00000"
    )

    assert result["error"] is True
    assert result["code"] == "STORE_NOT_FOUND"


async def test_inventory_404_returns_store_not_found(mock_hd_client):
    response = httpx.Response(404, request=httpx.Request("GET", "http://x"))
    mock_hd_client.check_inventory.side_effect = httpx.HTTPStatusError(
        "not found", request=response.request, response=response
    )

    result = await handle_check_inventory(
        mock_hd_client, item_id="100672337", store_id="999"
    )

    assert result["error"] is True
    assert result["code"] == "STORE_NOT_FOUND"


async def test_inventory_5xx_returns_api_error(mock_hd_client):
    response = httpx.Response(500, request=httpx.Request("GET", "http://x"))
    mock_hd_client.check_inventory.side_effect = httpx.HTTPStatusError(
        "server error", request=response.request, response=response
    )

    result = await handle_check_inventory(
        mock_hd_client, item_id="100672337", store_id="123"
    )

    assert result["error"] is True
    assert result["code"] == "API_ERROR"


async def test_find_store_error_during_zip_lookup_returns_api_error(mock_hd_client):
    response = httpx.Response(500, request=httpx.Request("GET", "http://x"))
    mock_hd_client.find_store.side_effect = httpx.HTTPStatusError(
        "server error", request=response.request, response=response
    )

    result = await handle_check_inventory(
        mock_hd_client, item_id="100672337", zip_code="78753"
    )

    assert result["error"] is True
    assert result["code"] == "API_ERROR"
