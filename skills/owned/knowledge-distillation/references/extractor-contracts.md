# Extractor Contracts

Every extractor is read-only with respect to source material and writes one candidate file. It must cite evidence IDs, distinguish quotation from paraphrase, and mark inference.

## Framework Extractor

Find repeatable decision sequences, diagnostic models, causal models, and named frameworks. Return:

```text
candidate_id:
claim:
steps_or_structure:
evidence_ids:
cross_domain_instances:
new_case_prediction:
limitations:
confidence:
```

Reject labels without an executable decision or procedure.

## Principle Extractor

Find rules, checklists, thresholds, and if-then heuristics. For every item record the condition, prescribed action, exception, evidence, and likely failure if misapplied.

## Case Extractor

Find actual applications. Record context, decision, action, result, confounders, hindsight limitations, and which candidate the case supports or contradicts.

## Counterexample Extractor

Find warnings, failed attempts, boundary cases, criticism, and conflicting evidence. Separate failures of the method from failures of implementation.

## Glossary Extractor

Find defined terms, overloaded words, aliases, dependencies, and disputed definitions. Do not treat ordinary vocabulary as source-specific terminology.

## Merge Contract

The synthesis agent may merge candidates only when their trigger, decision sequence, and boundary are materially the same. It must retain every source evidence ID and document the merge rationale.
