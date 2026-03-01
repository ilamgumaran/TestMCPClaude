"""Handler for the decompose_project MCP tool (Claude-powered).

This tool breaks a project description into a step-by-step shopping plan.
Claude (in the client UI) then calls search_products and find_services
separately for each item in the plan — one MCP call per need.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

_DECOMPOSE_SYSTEM = """\
You are a home improvement expert. Given a project or problem description, produce a
step-by-step shopping plan listing every product and professional service the customer
will need.

Rules:
- Each item is either type "product" (something bought from the store) or
  type "service" (professional installation, repair, or labor).
- Be specific with product queries — use terms a Home Depot search would understand.
- Include ALL consumables, fasteners, and tools, not just the main materials.
- List services when the project realistically requires a licensed professional
  (electrical, plumbing rough-in, structural, HVAC, etc.).
- Order items by the sequence a customer would shop for them.
- Limit to 10 items maximum.

Respond ONLY with a valid JSON object (no markdown fences, no explanation):
{
  "project_summary": "<one sentence summary of the project>",
  "difficulty": "diy" | "intermediate" | "professional",
  "shopping_plan": [
    {
      "step": <integer starting at 1>,
      "type": "product" | "service",
      "category": "<short category name>",
      "query": "<specific search term — omit for services>",
      "description": "<why this item is needed>",
      "tool_call": "search_products" | "find_services"
    }
  ],
  "notes": ["<safety tips, permits needed, or important caveats>"],
  "estimated_items": <total number of shopping_plan items>
}
"""


async def handle_decompose_project(
    anthropic_client: anthropic.AsyncAnthropic,
    model: str,
    project: str,
    zip_code: str | None = None,
    budget: float | None = None,
) -> dict[str, Any]:
    """Break a home improvement project into a step-by-step shopping plan.

    Returns a plan listing each product and service needed. The caller
    (Claude in the client UI) should then call search_products or
    find_services for each item in shopping_plan — one call per step.

    Args:
        project: Project or problem description
                 (e.g. "fix broken toilet", "rebuild kitchen cabinets")
        zip_code: Customer ZIP code — used to note whether local services apply
        budget: Optional total budget in USD to guide recommendations
    """
    if not project or not project.strip():
        return {
            "error": True,
            "code": "INVALID_PARAMS",
            "message": "project must be a non-empty description.",
        }

    user_content = f"Project: {project.strip()}"
    if budget is not None:
        user_content += f"\nBudget: ${budget:.2f}"
    if zip_code:
        user_content += f"\nLocation ZIP: {zip_code.strip()}"

    try:
        message = await anthropic_client.messages.create(
            model=model,
            max_tokens=1024,
            system=_DECOMPOSE_SYSTEM,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = message.content[0].text.strip()
        plan = json.loads(raw)
    except anthropic.APIError as exc:
        logger.error("Anthropic API error during decompose: %s", exc)
        return {
            "error": True,
            "code": "API_ERROR",
            "message": f"Anthropic API error: {exc}",
        }
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.error("Failed to parse decompose response: %s", exc)
        return {
            "error": True,
            "code": "API_ERROR",
            "message": "Failed to parse project decomposition from Claude.",
        }

    return {
        "project": project.strip(),
        "zip_code": zip_code,
        "budget": budget,
        **plan,
    }
