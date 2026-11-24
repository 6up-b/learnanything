---
title: Reader Tutor and Teach-Back
aliases:
  - Interaction Learning Surfaces
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-11-11
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/reader
  - src/learnloop/tutor
tags:
  - learnloop/concept
  - learnloop/reader
  - learnloop/tutor
  - learnloop/teach-back
---

# Reader Tutor and Teach-Back

Reader and tutor interactions help the learner understand source material without blurring instruction into assessment. Teach-back deliberately crosses that boundary only when it becomes a validated attempt.

## Reader

[[Concepts/Reader workbench|Reader workbench]] describes the desktop desks, the companion and the two ways pad writing reaches learner-text analysis or practice.

Reader views are anchored to extracted source spans. Learner questions can request direct answers, guided reasoning, or an ask-first response. Answers are citation-validated and bounded to the manifest. Owner-placed reading checks are source-visible instructional administrations and always skippable.

[[Concepts/Figures|Figures]] explains Show me from a passage, a question or both, including simulations and explanation videos, source protection and attempt-help accounting. Figures remain illustrations, never certification.

Reader signals may warm familiarity, burn a reserved surface when content is revealed (the detector reads every field the answer shows: the explanation, citation labels, the verified excerpt and the bridge, and records which one matched), or provide a short-lived routing prior. They never update posterior ability, FSRS, or certification. The reader is opt-in/dark by default (`tutor_qa.reader_enabled = false`).

## Tutor Q&A

Tutor answers are source-grounded and preserve provenance/citations. A cited passage costs the item what its chip shows (its label and, in the Ask panel, its excerpt; a Reader excerpt its verified quote), whichever branch delivered it, retrieval or the linked-passage fallback; opening the whole passage is the source viewer's own exposure record. "Ask the tutor" from a library ask made in a bound workbench session counts its help on that item, as the workbench's own Ask does. A margin cue's stored link is shown only while its passage is not a solution by effective role, the check discovery applies. A useful exchange can be promoted through an explicit reviewed workflow rather than silently becoming canonical practice content. Exposure propagation prevents later assessments from treating revealed material as cold.

## Teach-back

The learner gives an opening explanation; a provider plays a curious naïve student and asks planned questions one at a time. Planning is deterministic from diagnostic uncertainty and rubric criteria, with a transfer-tier question reserved when available. The entire transcript is graded as one `teach_back` attempt.

Only criteria actually asked and answered produce evidence. Unasked criteria are not zero-score failures. A transfer-tier criterion's evidence weighs `teach_back.transfer_evidence_multiplier` of a core one's, success and failure alike; in the canonical facet belief that holds from `mvp-0.59` (the facet-belief fixes); below it the canonical belief does not apply it. The planner's "uncertain facet first" reads per-LO facet uncertainty, which canonical vaults write and read from `mvp-0.59` too ([[Learner State and Projections#Facet uncertainty (diagnostic layer)]]). If the provider fails mid-conversation, completed turns can still be graded; if no follow-up was answered, the opening explanation is graded against core criteria. Conversation IDs make finish retry-safe.

## Safety boundaries

- Reader manifests exclude learner ability estimates and assessment-reserved content.
- AI output controls are sanitized before transcript persistence.
- Reader questions are interaction-policy signals, never ability evidence.
- Tutor exposure affects familiarity/independence.
- Teach-back uses the shared attempt application and coverage scaling.

## Modification guidance

- Add reader behavior as source-span events and explicitly state allowed evidence use.
- Add tutor capabilities through feature-owned contracts and citation validation.
- Add teach-back criteria through deterministic planning and asked-only grading.
- Preserve retry/dedup IDs and sidecar checkpoint serialization.

## Workflows and tests

- [[Reader to Practice Workflow]]
- [[Tutor and Teach-Back Workflow]]
- reader dialogue/capture/quick-check/restoration suites
- tutor QA/citation/promotion suites
- teach-back generation/conversation/checkpoint/simulation suites

