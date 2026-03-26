# Troubleshooting

Use this when the pipeline runs but coverage or outputs are weak.

## If a source fails

- verify whether it is supposed to be anonymous or keyed
- do not silently drop it
- log the failure mode in a coverage or status doc

## If retrieval size is large but relevance is poor

- the first fix is query design, not more scraping
- tighten themes and questions
- add failure-mode-specific queries
- add benchmark-specific queries

## If the system is too project-specific

- move assumptions into profile JSON or example docs
- keep scripts generic
- keep the target layout generic

## If the user wants completeness

Be explicit:

- say what is automated
- say what is blocked
- say what needs credentials
- say what still requires manual triage

Completeness in practice means “good enough for the current decision with explicit gap accounting,” not “no possible paper is missing.”
