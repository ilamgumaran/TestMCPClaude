"""Tests for handle_decompose_project."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import anthropic
import pytest

from hd_mcp.tools.project import handle_decompose_project


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _anthropic_message(text: str) -> MagicMock:
    msg = MagicMock()
    block = MagicMock()
    block.text = text
    msg.content = [block]
    return msg


DECOMPOSE_RESPONSE = json.dumps({
    "project_summary": "Replace broken toilet components to restore function.",
    "difficulty": "diy",
    "shopping_plan": [
        {
            "step": 1,
            "type": "product",
            "category": "plumbing",
            "query": "toilet flapper replacement kit",
            "description": "Main repair component that controls water flow.",
            "tool_call": "search_products",
        },
        {
            "step": 2,
            "type": "product",
            "category": "tools",
            "query": "adjustable wrench plumbing",
            "description": "Needed to tighten supply line connections.",
            "tool_call": "search_products",
        },
        {
            "step": 3,
            "type": "service",
            "category": "plumber",
            "query": None,
            "description": "Professional plumber if DIY is too complex.",
            "tool_call": "find_services",
        },
    ],
    "notes": ["Turn off water supply valve before starting."],
    "estimated_items": 3,
})


async def test_happy_path(mock_anthropic_client):
    mock_anthropic_client.messages.create.return_value = _anthropic_message(DECOMPOSE_RESPONSE)

    result = await handle_decompose_project(
        anthropic_client=mock_anthropic_client,
        model="claude-sonnet-4-6",
        project="fix broken toilet",
    )

    assert result["project"] == "fix broken toilet"
    assert result["difficulty"] == "diy"
    assert len(result["shopping_plan"]) == 3

    # Product steps should have tool_call = search_products
    product_steps = [s for s in result["shopping_plan"] if s["type"] == "product"]
    assert all(s["tool_call"] == "search_products" for s in product_steps)

    # Service steps should have tool_call = find_services
    service_steps = [s for s in result["shopping_plan"] if s["type"] == "service"]
    assert all(s["tool_call"] == "find_services" for s in service_steps)

    mock_anthropic_client.messages.create.assert_awaited_once()


async def test_zip_code_and_budget_in_prompt(mock_anthropic_client):
    mock_anthropic_client.messages.create.return_value = _anthropic_message(DECOMPOSE_RESPONSE)

    await handle_decompose_project(
        anthropic_client=mock_anthropic_client,
        model="claude-sonnet-4-6",
        project="fix broken toilet",
        zip_code="78753",
        budget=200.0,
    )

    call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
    user_content = call_kwargs["messages"][0]["content"]
    assert "78753" in user_content
    assert "$200.00" in user_content


async def test_zip_code_returned_in_response(mock_anthropic_client):
    mock_anthropic_client.messages.create.return_value = _anthropic_message(DECOMPOSE_RESPONSE)

    result = await handle_decompose_project(
        anthropic_client=mock_anthropic_client,
        model="claude-sonnet-4-6",
        project="fix broken toilet",
        zip_code="78753",
    )

    assert result["zip_code"] == "78753"


async def test_empty_project_returns_invalid_params(mock_anthropic_client):
    result = await handle_decompose_project(
        anthropic_client=mock_anthropic_client,
        model="claude-sonnet-4-6",
        project="",
    )

    assert result["error"] is True
    assert result["code"] == "INVALID_PARAMS"
    mock_anthropic_client.messages.create.assert_not_awaited()


async def test_anthropic_api_error_returns_api_error(mock_anthropic_client):
    mock_anthropic_client.messages.create.side_effect = anthropic.APIConnectionError(
        request=MagicMock()
    )

    result = await handle_decompose_project(
        anthropic_client=mock_anthropic_client,
        model="claude-sonnet-4-6",
        project="fix broken toilet",
    )

    assert result["error"] is True
    assert result["code"] == "API_ERROR"


async def test_invalid_json_from_claude_returns_api_error(mock_anthropic_client):
    mock_anthropic_client.messages.create.return_value = _anthropic_message("not json {{")

    result = await handle_decompose_project(
        anthropic_client=mock_anthropic_client,
        model="claude-sonnet-4-6",
        project="fix broken toilet",
    )

    assert result["error"] is True
    assert result["code"] == "API_ERROR"


async def test_project_with_services_for_complex_work(mock_anthropic_client):
    """Kitchen rebuild should produce service steps (licensed trades)."""
    kitchen_plan = json.dumps({
        "project_summary": "Full kitchen cabinet rebuild.",
        "difficulty": "professional",
        "shopping_plan": [
            {
                "step": 1, "type": "product", "category": "cabinets",
                "query": "kitchen base cabinet 30 inch",
                "description": "Main cabinet units.",
                "tool_call": "search_products",
            },
            {
                "step": 2, "type": "service", "category": "electrician",
                "query": None,
                "description": "Electrical outlet relocation.",
                "tool_call": "find_services",
            },
            {
                "step": 3, "type": "service", "category": "plumber",
                "query": None,
                "description": "Sink and dishwasher plumbing.",
                "tool_call": "find_services",
            },
        ],
        "notes": ["Permits may be required for electrical work."],
        "estimated_items": 3,
    })
    mock_anthropic_client.messages.create.return_value = _anthropic_message(kitchen_plan)

    result = await handle_decompose_project(
        anthropic_client=mock_anthropic_client,
        model="claude-sonnet-4-6",
        project="rebuild kitchen",
    )

    service_steps = [s for s in result["shopping_plan"] if s["type"] == "service"]
    assert len(service_steps) == 2
    assert result["difficulty"] == "professional"
    assert any("permit" in note.lower() for note in result["notes"])
