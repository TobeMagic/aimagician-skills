# Source Matrix

This matrix defines what the bundled system can do by default and where honesty boundaries matter.

| Source | Default status | Automation mode | Credentials |
|---|---|---|---|
| OpenAlex | ready | automated | no |
| arXiv | ready | automated | no |
| Crossref | ready | automated | no |
| CVF Open Access | ready | automated | no |
| Semantic Scholar | partial | automated with fallback skip | optional / often required |
| OpenReview | blocked or venue-specific | manual later | usually yes or constrained |
| ACL Anthology | manual or constrained | manual later | no |
| IEEE Xplore | manual | manual later | institutional or browser |
| Springer / ScienceDirect | manual | manual later | browser or institutional |

## Policy

- Start with anonymous, stable sources.
- Treat keyed or blocked sources as optional expansion layers.
- Never blur the line between “not covered” and “covered manually.”

## Practical meaning

If the user wants a no-key fully automatic system, the honest default is:

- OpenAlex
- arXiv
- Crossref
- CVF Open Access

Everything beyond that should be logged as optional or blocked unless the environment clearly supports it.
