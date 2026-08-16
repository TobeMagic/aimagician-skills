You are an independent plan reviewer. Do not call any tools or skills, do not
write files, and do not ask questions. Review only the supplied facts and
return a concise report.

Objective: Phase 50 will curate a local private Gaojie PPTX library before a
later PPTX agent uses it. The user requires exactly these 22 active category
directories: 003-封面模板, 036-目录模板, 037-章节模板, 038-标题模板,
039-结尾模板, 041-二段内容, 042-三段内容, 043-四段内容, 044-五段内容,
045-六段内容, 046-多段内容, 047-人物介绍, 048-荣誉奖项, 049-时间轴图,
050-架构流程, 051-商业模型, 052-样机展示, 053-金句模板, 054-合作伙伴,
057-优秀作品, 059-一段内容, 082-地图排版. There are 29 source category
directories and 377 packages total; the seven inactive directories are
055-图文排版, 056-表格图表, 058-实用素材, 062-风格配色, 104-数据基座,
105-文本组件 and 106-装饰形状. Inactive directories must be moved to a
private dated archive with source/post hashes and a recovery command; nothing
is deleted. Private bytes, credentials, original paths and images are never
committed. User permits Agnes to see rendered active-page PNGs only, not source
PPTX/media/credentials.

Phase 50 requirements:
- V7-CURATE-01: closed active/archive partition, dry-run, apply, verify and
  hash-matching recovery semantics.
- V7-CATALOG-01: deterministic private-only deck/page catalog with stable
  source-hash IDs, portable render/image-hash evidence and no source discovery
  during query.
- V7-VISION-01: strict normalized hash-bound visual observations with
  observation/inference/uncertainty fields; unavailable pages cannot be
  semantically retrieved.
- V7-REGION-01: OOXML-derived component regions with normalized geometry,
  editable source shapes, capacity, hierarchy and prohibited adaptations;
  image-only/unsafe/ambiguous regions rejected.
- V7-QUERY-01: deterministic bounded 3–6 candidates filtering only compiled
  catalog by mode (deck/page/region), role/tags/style/capacity/scope; result
  includes gates/reasons/scores and fails closed.

Plan tasks in order: (1) add schemas/tests then curation dry-run and only then
apply; (2) add deterministic catalog/region fixture tests and private smoke
compile; (3) validate schema then batch Agnes by rendered-image hash and local
contact-sheet sample inspection; (4) implement/query deterministic end-to-end
tracer; (5) focused/regression tests, no-private-tracked scan and fresh audit.
Existing Phase 49 `window_pptx` APIs remain unchanged. Component physical
assembly/adaptation is Phase 51; public rename/removal, skill rewrite and QA
are Phase 52; clean-room 15-page acceptance is Phase 53.

The plan additionally requires that every inactive package manifest record has
an opaque ID, original/archive relative locators, pre/post hashes, aggregate
tree digests and exact hash-guarded recovery operation; apply fails when any is
missing. The vision path has a private `opaque_page_id -> PNG/hash` mapping;
egress validators reject any source path/name, PPTX/media byte, credential-like
field or unknown field from prompts/responses. Equal query scores sort by
stable catalog ID ascending.

Return exactly. This is a PLAN review, not an implementation audit: mark a
requirement PASS when the plan has a concrete ordered implementation/test/
evidence path for it; mark FAIL only for an actual plan gap; never mark
NOT_RUN merely because implementation has not started.
1. five rows V7-CURATE-01 through V7-QUERY-01, each PASS/FAIL/NOT_RUN and
   a one-sentence reason;
2. findings as a table with only Blocker, Important or Nitpick;
3. `APPROVED` only when all five are PASS and there are zero Blocker/Important,
   otherwise `CHANGES_REQUIRED`;
4. one short stated residual risk.
