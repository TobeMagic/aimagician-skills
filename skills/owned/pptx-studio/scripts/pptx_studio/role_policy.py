"""Shared semantic page-capacity policy for governed PPTX assembly."""

from __future__ import annotations


# These are minimum *distinct client facts* and, before a client chooses a
# candidate, the same floor is the minimum number of independently bindable
# native text regions.  This keeps retrieval, composition and physical import
# aligned: a five-card template cannot be offered as a five-item page when
# the source has only one editable title box.
MIN_DISTINCT_CLIENT_FACTS_BY_ROLE: dict[str, int] = {
    "cover": 2,
    "contents": 5,
    "section": 2,
    "title": 2,
    "closing": 2,
    "one-item": 3,
    "two-item": 3,
    "three-item": 4,
    "four-item": 5,
    "five-item": 6,
    "six-item": 7,
    "multi-item": 6,
    "team": 4,
    "awards": 4,
    "timeline": 5,
    "process": 5,
    "flow": 5,
    "business-model": 5,
    "comparison": 5,
    "matrix": 5,
    "roadmap": 5,
    "dashboard": 6,
    "data": 4,
    "table": 4,
    "product": 4,
    "quote": 2,
    "partners": 4,
    "case-study": 4,
    "map": 4,
}


def minimum_distinct_client_facts(role: object) -> int:
    """Return the governed semantic-content floor for a declared role."""

    return MIN_DISTINCT_CLIENT_FACTS_BY_ROLE.get(str(role), 2)
