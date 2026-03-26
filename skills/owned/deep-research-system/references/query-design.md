# Query Design

Use this reference when designing a reusable `profile` or `query_registry`.

## Goal

The query layer should be reusable across directions, not tied to one exact project name.

A good query design balances:

- direct method retrieval
- adjacent alternatives
- failure-mode repair modules
- evaluation protocol discovery
- venue and application narrative

## Minimum theme set

For a serious research direction, cover at least these five theme classes:

1. core method
2. strong alternatives
3. failure-mode-specific modules
4. benchmarks and evaluation
5. venue-facing or application-facing narrative

## Good query shape

Each query entry should answer:

- what theme this covers
- what question it is trying to answer
- how that question maps to each source

That is why the starter registry uses:

- `id`
- `theme`
- `question`
- `openalex`
- `arxiv`
- `crossref`

## Reuse rule

When adapting to a new direction:

- keep the schema
- change the themes and questions
- write outputs to a new root or run directory

Avoid baking project-specific assumptions into the scripts themselves.

## Typical mistakes

- only querying the exact method name
- ignoring failure-mode modules
- ignoring benchmark papers
- using very broad generic terms with no decision value
- forgetting to encode the actual research question
