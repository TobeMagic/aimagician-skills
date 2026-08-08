TASK_ID: phase38-reference-art-direction-inspection
ROLE: visual-inspector
TASK_TYPE: discovery
MODALITY: vision
OBJECTIVE: Extract a reusable, implementation-ready ArtDirectionProfile and page-family grammar from the attached 15-slide user-accepted work-summary reference, separating observable design logic from protected or content-specific identity.
DELIVERABLE: A pixel-evidence report that can directly constrain TemplatePack v2, Registry v3 retrieval, and Phase 39 flagship generation.
REVIEW_POINT: .planning/evidence/phase38-reference-baseline/contact-sheet.png rendered from the exact SHA-256-matching authorized reference.

SOURCE_OF_TRUTH:
- Attached .planning/evidence/phase38-reference-baseline/contact-sheet.png
- .planning/REQUESTS.md USR-V6-04, USR-V6-06, USR-V6-07
- .planning/phases/38-window-pptx-v6-template-intelligence/38-SPEC.md

ORIGINAL_REQUESTS:
- USR-V6-04: complete cover/directory/chapter/body/conclusion/ending anatomy.
- USR-V6-06: match reference hierarchy, rhythm, motif continuity, visual richness, data presentation, and complete-work polish.
- USR-V6-07: avoid shallow cards and redundant repair; use better motifs, imagery, diagrams, and bounded correction.

ACCEPTED_DECISIONS:
- The attached reference is user-authorized and already packaged as one TemplatePack v1.
- Extract and recombine design logic; do not require copying its specific organization, wording, photos, or decorative identity.
- Native editable PPTX is canonical; whole-slide rasterization is prohibited.
- Engineering metrics cannot replace pixel-level judgment.

KNOWN_CONTEXT:
- The contact sheet contains all 15 slides in reading order.
- Package metadata: one master, three layouts, 29 media objects, four editable charts.
- Phase 38 must create template intelligence that later supports a 28+4 work-report flagship and campus/academic flagships.

REQUIRED_SKILLS:
- cli-agent-delegator: apply visual-inspection evidence and scope protocol.
- aimagician-superpower: preserve original-request traceability and phase boundaries.
- skill-creator: translate the visual findings into a governed owned-Skill capability contract.
- interface-design: analyze hierarchy, grid, typography, color, motifs, imagery, data visualization, pacing, and production polish.

Before substantive work, load every skill named in REQUIRED_SKILLS and report the loaded skill IDs. Apply their workflows and boundaries. You have access to the same installed owned skills as the controller. If any required skill or source of truth cannot be loaded, return NEEDS_CONTEXT with the missing item; do not substitute an improvised workflow.

ALLOWED_SCOPE:
- Read the attached image and the three named local planning documents.
- Describe visible regions and compare slide families within the sheet.

FORBIDDEN_SCOPE:
- No writes, code execution, git mutation, network access, secret/private access, OCR claims not supported by pixels, or visual score for any generated candidate.
- Do not claim the reference is universally excellent; identify both target qualities and weaknesses that should not be copied.

PERMISSION_MODE: strict-read-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: Read-only document reads only; no shell required.
TESTS_AND_EVIDENCE: Cite slide numbers/regions for every material visual claim.
GIT_POLICY: inspect-only
MODEL_POLICY: Agnes visual
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: skill loading; full-sheet scan; anatomy/rhythm analysis; page-family grammar; token/motif extraction; anti-patterns; implementation checklist.
STOP_AND_ESCALATE_WHEN: The image cannot be loaded at readable resolution or a required skill/source is unavailable.
SESSION_EXPORT: NONE
OUTPUT_FORMAT: Skills loaded; observable visual evidence; deck anatomy and pacing map; reusable art-direction tokens; page-family catalog with capacity/semantic fit; motif/choreography rules; chart/table/image rules; anti-patterns not to copy; TemplatePack v2 metadata fields; Registry v3 retrieval features; Phase 39 acceptance checklist; findings; status/model/session ID.
