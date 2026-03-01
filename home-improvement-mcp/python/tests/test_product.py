"""Tests for handle_get_product."""

from __future__ import annotations

import httpx
import pytest

from hd_mcp.tools.product import handle_get_product


async def test_happy_path(mock_hd_client):
    result = await handle_get_product(mock_hd_client, item_id="100672337")

    assert result["item_id"] == "100672337"
    assert result["name"] == "DEWALT 20V MAX Cordless Drill"
    assert result["brand"] == "DEWALT"
    assert result["price"] == 149.00
    assert result["original_price"] == 179.00
    assert result["model_number"] == "DCD771C2"

    mock_hd_client.get_product.assert_awaited_once_with(
        item_id="100672337", store_id=None
    )


async def test_store_id_passed_through(mock_hd_client):
    await handle_get_product(mock_hd_client, item_id="100672337", store_id="6315")

    mock_hd_client.get_product.assert_awaited_once_with(
        item_id="100672337", store_id="6315"
    )


async def test_item_id_stripped(mock_hd_client):
    await handle_get_product(mock_hd_client, item_id="  100672337  ")

    mock_hd_client.get_product.assert_awaited_once_with(
        item_id="100672337", store_id=None
    )


async def test_empty_item_id_returns_invalid_params(mock_hd_client):
    result = await handle_get_product(mock_hd_client, item_id="")

    assert result["error"] is True
    assert result["code"] == "INVALID_PARAMS"
    mock_hd_client.get_product.assert_not_awaited()


async def test_404_returns_product_not_found(mock_hd_client):
    response = httpx.Response(404, request=httpx.Request("GET", "http://x"))
    mock_hd_client.get_product.side_effect = httpx.HTTPStatusError(
        "not found", request=response.request, response=response
    )

    result = await handle_get_product(mock_hd_client, item_id="999999")

    assert result["error"] is True
    assert result["code"] == "PRODUCT_NOT_FOUND"
    assert "999999" in result["message"]


async def test_5xx_returns_api_error(mock_hd_client):
    response = httpx.Response(500, request=httpx.Request("GET", "http://x"))
    mock_hd_client.get_product.side_effect = httpx.HTTPStatusError(
        "server error", request=response.request, response=response
    )

    result = await handle_get_product(mock_hd_client, item_id="100672337")

    assert result["error"] is True
    assert result["code"] == "API_ERROR"
    assert "500" in result["message"]


async def test_network_error_returns_api_error(mock_hd_client):
    mock_hd_client.get_product.side_effect = httpx.ConnectError("timeout")

    result = await handle_get_product(mock_hd_client, item_id="100672337")

    assert result["error"] is True
    assert result["code"] == "API_ERROR"


async def test_images_extracted(mock_hd_client):
    result = await handle_get_product(mock_hd_client, item_id="100672337")

    assert isinstance(result["images"], list)
    assert "homedepot-static.com" in result["images"][0]
