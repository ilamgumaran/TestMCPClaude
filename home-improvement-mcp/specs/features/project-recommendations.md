# Feature: Project-Based Product Recommendations

**ID**: F-03
**Requirement**: FR-03
**Use Cases**: UC-03

## Summary

As an MCP client, I want to provide a free-text project description and receive a
categorized list of relevant Home Depot products so that I can guide the user through
planning and sourcing their project.

## Scope

- Natural language project description as input
- AI-driven category decomposition using `claude-sonnet-4-6`
- Parallel product search per category
- AI-driven result curation and ranking
- Optional budget-aware filtering
- Optional store preference for in-stock prioritization

## Out of Scope

- Quantity estimation or bill-of-materials generation (future feature)
- Cost breakdown / project budgeting (future feature)
- Installation instructions or how-to guides
