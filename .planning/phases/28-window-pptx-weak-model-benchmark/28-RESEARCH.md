# Phase 28 Research: Controlled PPTX Skill Evaluation

## Experimental Unit

One trial is the immutable tuple `(benchmark_version, scenario_id, arm_id, model_id, repeat_index)`. Its identifier and seed derive from canonical JSON so reruns cannot silently change grouping or randomization.

## Arms

1. `unassisted-json`: a minimal output contract with no archetype, mapping, design-registry, or QA guidance. Invalid or non-JSON output is a measured failure, not repaired by the harness.
2. `governed-plan`: the model receives the strict DeckPlan contract, scenario-safe structure choices, and weak-model step sequence; deterministic compilation is evaluated, but candidate QA/repair is not credited.
3. `full-v5`: the same governed planning input continues through registry-bound render planning, native-object rendering, five-layer QA, bounded repair, and transaction evidence.

The prompt prefix, scenario brief, model identity, repeat count, and token budget remain frozen within an arm. Provider metadata is recorded rather than normalized away.

## Scenario Coverage

The corpus covers business reporting, project proposal, product launch, market analysis, sales proposal, investor pitch, annual review, strategic planning, data analysis, research report, training, brand introduction, project kickoff, operations retrospective, and e-commerce/marketing planning.

Each scenario contains an audience, decision objective, required narrative beats, key facts with stable fact IDs, prohibited inventions, expected archetype, expected semantic forms, slide-count range, language, and asset availability. Content is synthetic and license-safe.

## Scoring

Deterministic scores include response validity, DeckPlan validity, fact retention, prohibited-claim violations, compile success, capacity/splitting compliance, family/layout diversity, native/editable coverage, hard-gate pass, artifact completeness, and repeat agreement. A missing output receives no imputed score.

Blind human review uses anonymized trial labels and a stable rubric: narrative clarity, content accuracy, visual hierarchy, layout fitness/variety, readability, chart/diagram appropriateness, brand consistency, editability, and customer-delivery readiness. Reviewers must not see arm or model identity.

## Release Thresholds

- all 15 scenarios represented in the frozen corpus;
- 100% manifest/hash verification for recorded artifacts;
- at least 95% full-v5 DeckPlan validity and compile success across available trials;
- at least 95% full-v5 customer hard-gate pass after repair on native Windows evidence;
- at least 95% fact retention with zero prohibited numeric invention in release candidates;
- full-v5 deterministic composite at least 15 points above unassisted and 8 above governed-plan;
- full-v5 customer-delivery human score at least 4.0/5 and at least 0.5 above unassisted;
- repeat standard deviation no greater than 0.35/5 for customer-delivery review;
- no unresolved Critical or Important audit finding.

Provider unavailability does not lower thresholds; it leaves the benchmark incomplete.
