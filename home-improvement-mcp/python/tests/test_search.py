"""Tests for handle_search_products."""

from __future__ import annotations

import httpx
import pytest

from hd_mcp.tools.search import _build_keyword, handle_search_products


# ---------------------------------------------------------------------------
# _build_keyword unit tests (pure function — no mock needed)
# ---------------------------------------------------------------------------

def test_keyword_query_only():
    assert _build_keyword("drill", None, None, None, None, None, None, None) == "drill"


def test_keyword_category_prepended():
    kw = _build_keyword("drill", "power tools", None, None, None, None, None, None)
    assert kw == "power tools drill"


def test_keyword_product_types_as_separate_words():
    kw = _build_keyword(
        "drill",
        category=None,
        product_types=["hammer drill", "SDS drill"],
        brand=None, model=None, features=None, material=None, color=None,
    )
    assert kw == "hammer drill SDS drill drill"


def test_keyword_features_as_separate_words():
    kw = _build_keyword(
        "drill",
        category=None, product_types=None, brand=None, model=None,
        features=["cordless", "brushless", "20V MAX"],
        material=None, color=None,
    )
    assert kw == "drill cordless brushless 20V MAX"


def test_keyword_full_combination():
    kw = _build_keyword(
        query="drill",
        category="power tools",
        product_types=["hammer drill", "rotary hammer"],
        brand="DEWALT",
        model="DCD999B",
        features=["cordless", "brushless"],
        material="stainless steel",
        color="yellow",
    )
    # Order: category | product_types | query | features | material | color | model | brand
    assert kw == "power tools hammer drill rotary hammer drill cordless brushless stainless steel yellow DCD999B DEWALT"


def test_keyword_skips_empty_strings_in_lists():
    kw = _build_keyword(
        "paint",
        category=None,
        product_types=["  ", "exterior paint", ""],
        brand=None, model=None, features=None, material=None, color=None,
    )
    assert kw == "exterior paint paint"


# ---------------------------------------------------------------------------
# handle_search_products integration tests
# ---------------------------------------------------------------------------

async def test_happy_path(mock_hd_client):
    result = await handle_search_products(mock_hd_client, query="drill")

    assert result["query"] == "drill"
    assert result["total_from_api"] == 42
    assert len(result["products"]) == 1
    product = result["products"][0]
    assert product["item_id"] == "100672337"
    assert product["name"] == "DEWALT 20V MAX Cordless Drill"
    assert product["price"] == 149.00

    mock_hd_client.search_products.assert_awaited_once_with(
        keyword="drill",
        page_size=10,
        start_index=0,
        store_id=None,
        sort_by=None,
    )


async def test_product_types_in_keyword(mock_hd_client):
    await handle_search_products(
        mock_hd_client,
        query="drill",
        product_types=["hammer drill", "SDS drill"],
    )

    call_kwargs = mock_hd_client.search_products.call_args.kwargs
    assert "hammer drill" in call_kwargs["keyword"]
    assert "SDS drill" in call_kwargs["keyword"]
    assert "drill" in call_kwargs["keyword"]


async def test_product_types_reflected_in_filters(mock_hd_client):
    result = await handle_search_products(
        mock_hd_client,
        query="valve",
        product_types=["flapper", "fill valve", "flush valve"],
    )

    assert result["filters"]["product_types"] == ["flapper", "fill valve", "flush valve"]


async def test_brand_in_keyword_and_filters(mock_hd_client):
    result = await handle_search_products(mock_hd_client, query="drill", brand="DEWALT")

    call_kwargs = mock_hd_client.search_products.call_args.kwargs
    assert "DEWALT" in call_kwargs["keyword"]
    assert result["filters"]["brand"] == "DEWALT"


async def test_model_in_keyword(mock_hd_client):
    await handle_search_products(mock_hd_client, query="drill", model="DCD771C2")

    call_kwargs = mock_hd_client.search_products.call_args.kwargs
    assert "DCD771C2" in call_kwargs["keyword"]


async def test_features_each_as_separate_keyword_words(mock_hd_client):
    await handle_search_products(
        mock_hd_client, query="drill", features=["cordless", "brushless", "20V MAX"]
    )

    call_kwargs = mock_hd_client.search_products.call_args.kwargs
    kw = call_kwargs["keyword"]
    assert "cordless" in kw
    assert "brushless" in kw
    assert "20V MAX" in kw


async def test_material_and_color_in_keyword(mock_hd_client):
    await handle_search_products(
        mock_hd_client, query="faucet", material="stainless steel", color="brushed nickel"
    )

    kw = mock_hd_client.search_products.call_args.kwargs["keyword"]
    assert "stainless steel" in kw
    assert "brushed nickel" in kw


async def test_keyword_sent_echoed_in_response(mock_hd_client):
    result = await handle_search_products(
        mock_hd_client,
        query="drill",
        category="power tools",
        brand="DEWALT",
        features=["cordless"],
    )

    assert result["keyword_sent"] == "power tools drill cordless DEWALT"


async def test_min_price_filter(mock_hd_client):
    result = await handle_search_products(mock_hd_client, query="drill", min_price=200.0)

    # Sample product is $149 — should be filtered out
    assert result["total_after_filters"] == 0
    assert result["products"] == []


async def test_max_price_filter(mock_hd_client):
    result = await handle_search_products(mock_hd_client, query="drill", max_price=100.0)

    assert result["total_after_filters"] == 0


async def test_max_price_passes_matching_product(mock_hd_client):
    result = await handle_search_products(mock_hd_client, query="drill", max_price=200.0)

    assert result["total_after_filters"] == 1


async def test_min_rating_filter(mock_hd_client):
    # Sample product rating is 4.8 — passes a 4.5 floor
    result = await handle_search_products(mock_hd_client, query="drill", min_rating=4.5)
    assert result["total_after_filters"] == 1

    # Fails a 5.0 floor
    result = await handle_search_products(mock_hd_client, query="drill", min_rating=5.0)
    assert result["total_after_filters"] == 0


async def test_price_filter_excludes_null_price(mock_hd_client):
    mock_hd_client.search_products.return_value = {
        "searchReport": {"totalProducts": 1},
        "products": [{"itemId": "x", "nowPrice": None}],
    }

    result = await handle_search_products(mock_hd_client, query="drill", max_price=100.0)

    # Product with no price is excluded when a price filter is active
    assert result["total_after_filters"] == 0


async def test_pagination(mock_hd_client):
    await handle_search_products(mock_hd_client, query="lumber", page=3, page_size=5)

    call_kwargs = mock_hd_client.search_products.call_args.kwargs
    assert call_kwargs["start_index"] == 10  # (3-1) * 5
    assert call_kwargs["page_size"] == 5


async def test_empty_query_returns_invalid_params(mock_hd_client):
    result = await handle_search_products(mock_hd_client, query="")

    assert result["error"] is True
    assert result["code"] == "INVALID_PARAMS"
    mock_hd_client.search_products.assert_not_awaited()


async def test_whitespace_query_returns_invalid_params(mock_hd_client):
    result = await handle_search_products(mock_hd_client, query="   ")

    assert result["error"] is True
    assert result["code"] == "INVALID_PARAMS"


async def test_api_4xx_returns_api_error(mock_hd_client):
    response = httpx.Response(400, request=httpx.Request("GET", "http://x"))
    mock_hd_client.search_products.side_effect = httpx.HTTPStatusError(
        "bad request", request=response.request, response=response
    )

    result = await handle_search_products(mock_hd_client, query="drill")

    assert result["error"] is True
    assert result["code"] == "API_ERROR"
    assert "400" in result["message"]


async def test_network_error_returns_api_error(mock_hd_client):
    mock_hd_client.search_products.side_effect = httpx.ConnectError("timeout")

    result = await handle_search_products(mock_hd_client, query="drill")

    assert result["error"] is True
    assert result["code"] == "API_ERROR"


async def test_zip_code_resolves_store(mock_hd_client):
    result = await handle_search_products(mock_hd_client, query="drill", zip_code="78753")

    mock_hd_client.find_store.assert_awaited_once_with(zip_code="78753", radius=25)
    call_kwargs = mock_hd_client.search_products.call_args.kwargs
    assert call_kwargs["store_id"] == "123"


async def test_zip_lookup_failure_is_nonfatal(mock_hd_client):
    response = httpx.Response(500, request=httpx.Request("GET", "http://x"))
    mock_hd_client.find_store.side_effect = httpx.HTTPStatusError(
        "error", request=response.request, response=response
    )

    result = await handle_search_products(mock_hd_client, query="drill", zip_code="99999")

    assert not result.get("error")
    call_kwargs = mock_hd_client.search_products.call_args.kwargs
    assert call_kwargs["store_id"] is None


async def test_store_id_takes_precedence_over_zip(mock_hd_client):
    await handle_search_products(
        mock_hd_client, query="drill", store_id="6315", zip_code="78753"
    )

    mock_hd_client.find_store.assert_not_awaited()
    call_kwargs = mock_hd_client.search_products.call_args.kwargs
    assert call_kwargs["store_id"] == "6315"


async def test_empty_products_list(mock_hd_client):
    mock_hd_client.search_products.return_value = {
        "searchReport": {"totalProducts": 0},
        "products": [],
    }

    result = await handle_search_products(mock_hd_client, query="unobtainium")

    assert result["total_from_api"] == 0
    assert result["total_after_filters"] == 0
    assert result["products"] == []


async def test_sort_and_store_passed_through(mock_hd_client):
    await handle_search_products(
        mock_hd_client, query="paint", store_id="6315", sort_by="price_asc"
    )

    call_kwargs = mock_hd_client.search_products.call_args.kwargs
    assert call_kwargs["store_id"] == "6315"
    assert call_kwargs["sort_by"] == "price_asc"
