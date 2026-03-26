# ActiveVLM Case Study

This skill was extracted from a real docs-first research system used to study `ActiveVLM`.

That case study established three useful design principles:

## 1. Query the innovation space, not just the exact current method

The strongest research directions did not come only from searching for the exact current method name.
Useful themes included:

- active perception
- scene graphs
- memory and backtracking
- stop or termination verification
- world models
- service-robot narrative

## 2. A reusable system is more valuable than a one-off search

The original project eventually needed:

- repeated second-pass searches
- source expansion
- innovation maps
- venue-facing recommendations

That only worked because retrieval scripts, profiles, matrices, and docs lived together.

## 3. Honesty about coverage matters

The project benefited from explicitly stating:

- which sources were automated
- which sources required credentials
- which conclusions were strong
- which conclusions were still directional

This is why the system includes a coverage gap register by design.
