# Systematic Review Protocol

Use this when the user wants the work to feel closer to a systematic review rather than an ad hoc search.

## Core questions

Before running retrieval, define:

1. what decision this review must support
2. which bottleneck or uncertainty triggered the review
3. what counts as inclusion
4. what counts as exclusion

## Inclusion examples

- direct method papers
- closely adjacent methods
- module papers that attack the current failure mode
- benchmark or evaluation papers
- venue-relevant systems papers

## Exclusion examples

- papers unrelated to the target domain
- weakly related survey noise with no decision value
- papers that only match one generic keyword but not the real problem

## Source layers

### Layer A: default automated

- OpenAlex
- arXiv
- Crossref
- CVF Open Access

### Layer B: optional or constrained

- Semantic Scholar
- OpenReview
- ACL Anthology
- IEEE Xplore
- Springer / ScienceDirect

## Stopping rule

You can say the review is “sufficient for decision-making” when:

1. multi-source retrieval is complete
2. the processed matrix exists
3. the main themes are stable
4. the next experiment or paper decision is clear
5. remaining coverage gaps are explicitly logged

This still does not mean the literature is exhaustive.
