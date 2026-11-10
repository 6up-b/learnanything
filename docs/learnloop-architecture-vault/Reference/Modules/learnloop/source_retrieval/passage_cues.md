---
title: "learnloop.source_retrieval.passage_cues"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/passage_cues.py"
source_paths:
  - "src/learnloop/source_retrieval/passage_cues.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.passage_cues module"
  - "src/learnloop/source_retrieval/passage_cues.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.passage_cues`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.passage_cues` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Reader workbench RW3b: discovered cues (spec_reader_workbench_v1 §6.2 items 1-6, §6.3, §6.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py) |
| Source lines | 1760 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `models_off() -> bool` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 161)
- `class CueDiscoveryError(ValueError)` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 167) — A refused discovery or tap (nothing was written).
- `discovery_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 179) — RW3b's switch, under RW3a's kill switch.
- `try_first_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 185)
- `value_order_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 190)
- `holdout_rate(vault: LoadedVault) -> float` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 194) — ``cues.holdout_rate`` normalized once (clamped to [0, 0.99]): the one value both the draw and the stored propensity use (Codex verify F18).
- `class CueTarget` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 207) — One thing a cue can connect to, rendered as its LLM-written statement.
  - `open(self) -> bool` (line 230; public)
  - `state_key(self) -> str` (line 234; public) — The cache key: the target's statement and status (§6.2 item 5).
  - `ref(self) -> str` (line 240; public)
  - `left_id(self, extraction_id: str) -> str` (line 243; public)
  - `describe(self) -> dict[str, Any]` (line 246; public)
- `source_learning_objects(vault: LoadedVault, repository: Repository, extraction_id: str) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 252) — The LOs the open source teaches: provenance-linked to a section (RW6a's reading), or linked to one of its passages by a teaching link.
- `unchecked_claims(vault: LoadedVault, repository: Repository, extraction_id: str, *, now: Any | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 538) — RW6a's "claims needing an independent check" (§9.1) on this source: facets whose work in the current or the previous reader session was assisted only, with no unassisted success since (``recap.session_summary``, a pure read).
- `cue_targets(vault: LoadedVault, repository: Repository, extraction_id: str, *, failure: Callable[[str | None], float | None] | None=None) -> list[CueTarget]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 601) — Every target the open source's cues can connect to (reads only).
- `targets_key(targets: Sequence[CueTarget]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 652) — One fingerprint of the targets' states: the Reader asks for discovery again when it changes (a new or resolved hypothesis in the session).
- `class Protection` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 664) — What of one extraction a model may never read, from the shared helpers.
  - `allows(self, key: tuple[str, str]) -> bool` (line 671; public)
- `protection(vault: LoadedVault, repository: Repository, extraction_id: str) -> Protection` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 675) — T6's exclusions (``teaching_exclusions``: exam and held-out material, source-set roles without teaching authority, exercise and assessment links) and the held-out partition (``held_out_material``).
- `class SpanLearningObjects` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 692) — The LOs a passage teaches: its section's provenance-linked LOs (the Guide's reading) and the LOs a teaching link names this very block for.
  - `__init__(self, vault: LoadedVault, repository: Repository, extraction_id: str) -> None` (line 696; internal)
  - `__call__(self, span_id: str) -> list[str]` (line 713; internal)
- `contrast_list(vault: LoadedVault, repository: Repository, target: CueTarget, extraction_id: str, *, guard: Protection | None=None) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 728) — Passages with a ``contrast`` or ``counterexample`` role on the target's LOs or their confusables: RW4e's proposals (the sources spec's ``remediate`` list) and the roles this judge proposed before.
- `class Shortlist` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 783)
  - `manifest(self) -> dict[str, Any]` (line 793; public)
- `shortlist(vault: LoadedVault, repository: Repository, target: CueTarget, extraction_id: str, *, guard: Protection | None=None, embedder: Any | None=None, limit: int=SHORTLIST, owner_id: str='', deep: bool=True, budget: SpendBudget | None=None) -> Shortlist` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 798) — The target's shortlisted passages, every one protected before a model sees it.
- `class CueJudgment(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 855)
  - `_tolerate_roles(cls, data: Any) -> Any` (line 871; internal)
- `class CueJudgeResult(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 875)
- `judge_prompt(target: CueTarget, candidates: Sequence[Mapping[str, Any]]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 911)
- `quote_verifies(quote: str, text: str) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 922) — The quote is this passage's own words (canonical text, RW1c's helper).
- `discovery_calls_last_24h(repository: Repository, extraction_id: str, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 959) — The cue judge's requests for this source in the last 24 hours (a rolling window in UTC), counted from the durable receipts (Codex verify F16): one root receipt per request, written before it is sent, a failed, unfinished or retried one included.
- `discovery_budget(vault: LoadedVault, *, cancelled: Callable[[], bool] | None=None) -> SpendBudget` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 995) — The judge's caps for one whole discovery (one source open), shared by every target (Codex review F3): each admitted judge request counts once, a failure and a retry included, against ``cues.max_calls_per_source_open``; metered dollars against ``cues.max_daily_cost_usd``.
- `judge_target(vault: LoadedVault, repository: Repository, listed: Shortlist, extraction_id: str, *, client: Any | None=None, clock: Clock | None=None, budget: SpendBudget | None=None, route: Any | None=None, envelope: SharedDailyEnvelope | None=None, admit: Callable[[SpendEstimate], None] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1034) — One listwise judgment of a target's shortlist; picks become links.
- `discover(vault: LoadedVault, repository: Repository, extraction_id: str, *, client: Any | None=None, embedder: Any | None=None, clock: Clock | None=None, dry_run: bool=False, cancelled: Callable[[], bool]=lambda: False, budget: SpendBudget | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1247) — Compute the open source's missing links, at most ``cues.max_calls_per_source_open`` judge requests in all (a failure and a retry count), highest ``p_open`` first.
- `holdout_draw(link_id: str, rate: float) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1378) — The seeded draw for one link: reproducible from its seed (G14).
- `discovered_candidates(vault: LoadedVault, repository: Repository, *, extraction_id: str, plan: Mapping[str, Any], targets: Sequence[CueTarget], failure: Callable[[str | None], float | None]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1436) — The current links of the current targets as cue candidates (reads only).
- `seen_targets(vault: LoadedVault, repository: Repository, *, extraction_id: str, candidates: Sequence[Mapping[str, Any]], now: str | None=None) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1516) — The targets whose cue the learner actually had in view during this visit (Codex review F10): the shown impressions of the current reader session on this source (impressions less than ``SESSION_GAP`` apart, the newest less than that before ``now``; RW6a's session), read back to t…
- `targets_pending(vault: LoadedVault, repository: Repository) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1561) — Background work that can name a new target (Codex review F8): a learner-text gap job queued or running.
- `merged_cues(vault: LoadedVault, repository: Repository, *, extraction_id: str, plan: Mapping[str, Any], now: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1574) — RW3a's cue payload with RW3b's discovered cues merged in (reads only).
- `find_discovered(vault: LoadedVault, repository: Repository, *, extraction_id: str, cue_id: str, plan: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1701) — A discovered cue of this source by id, whatever the learner's choices (a "not relevant" can be undone); held-out material is never one.

### Module constants

- `PROMPT_VERSION` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 106)
- `CUES_VERSION` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 107)
- `TARGET_LEFT_KIND` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 109)
- `SPAN_RIGHT_KIND` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 110)
- `TARGET_RIGHT_KIND` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 112)
- `TARGET_KINDS` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 113)
- `OPEN_TARGET_KINDS` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 118)
- `TRY_FIRST_ONLY_KINDS` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 121)
- `RELATIONS` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 122)
- `LINK_RELATIONS` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 123)
- `KIND_FOR_RELATION` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 125)
- `CONFIDENCES` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 127)
- `CONTRAST_ROLES` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 129)
- `SHORTLIST` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 131)
- `PASSAGE_CHARS` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 132)
- `STATEMENT_CHARS` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 133)
- `PICK_AT_MOST` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 134)
- `MIN_QUOTE_CHARS` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 136)
- `JUDGE_ENVELOPE` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 137)
- `HOLDOUT_SALT` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 139)
- `P_OPEN_SOURCES` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 141)
- `NOTE_PREREQUISITE` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 145)
- `NOTE_APPLICATION` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 146)
- `NOTE_TRY_FIRST` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 147)
- `BECAUSE_WORK` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 148)
- `BECAUSE_QUESTION` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 149)
- `BECAUSE_SHOWN` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 150)
- `BECAUSE_CLAIM` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 151)
- `DISCOVERED_TEMPLATES` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 152)
- `MODELS_ENV` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 158)
- `CUE_JUDGE_TASK` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 882)
- `_INSTRUCTIONS` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 893)
- `DAILY_CAP_REASON` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 941)
- `DAILY_CAP_WINDOW` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 945)
- `MAX_LEARNER_TEXT_CHARS` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1410)
- `_PRIVATE` ([src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1694)

### Explicit exports

`__all__` declares:

- `BECAUSE_CLAIM`
- `BECAUSE_QUESTION`
- `BECAUSE_SHOWN`
- `BECAUSE_WORK`
- `CONTRAST_ROLES`
- `CUES_VERSION`
- `CUE_JUDGE_TASK`
- `CueDiscoveryError`
- `CueJudgeResult`
- `CueJudgment`
- `CueTarget`
- `DISCOVERED_TEMPLATES`
- `KIND_FOR_RELATION`
- `MODELS_ENV`
- `NOTE_APPLICATION`
- `NOTE_PREREQUISITE`
- `NOTE_TRY_FIRST`
- `PROMPT_VERSION`
- `RELATIONS`
- `RoleProposal`
- `TARGET_LEFT_KIND`
- `TARGET_RIGHT_KIND`
- `contrast_list`
- `cue_targets`
- `discover`
- `discovery_calls_last_24h`
- `discovered_candidates`
- `discovery_enabled`
- `find_discovered`
- `holdout_draw`
- `holdout_rate`
- `judge_prompt`
- `judge_target`
- `merged_cues`
- `protection`
- `seen_targets`
- `targets_pending`
- `unchecked_claims`
- `quote_verifies`
- `shortlist`
- `source_learning_objects`
- `targets_key`
- `try_first_enabled`
- `value_order_enabled`

## Internal implementation anchors

- `_cues(vault: LoadedVault) -> Any` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 175)
- `_topic(vault: LoadedVault, lo_id: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 270)
- `_clip(text: str | None, limit: int) -> str` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 275)
- `_sigmoid(value: float) -> float` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 280)
- `class _Failure` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 285) — The active predictor's P(failure) per LO, read once (``placement.predictor``).
- `_misconception_status(record: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 319)
- `_flat(text: str | None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 323)
- `_facets(*groups: Any) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 327)
- `class _Provenance` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 337) — Reads of the rows a target was named from (one read per id).
- `_episode_targets(vault: LoadedVault, repository: Repository, lo_id: str, topic: str, reads: _Provenance) -> list[CueTarget]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 377) — An open probe episode's concrete hypotheses, each with its posterior mass (§6.2 item 4: "the open episode's posterior"): a registry hypothesis by its misconception's statement, a legacy one by the statement of the error event it was entered from (Codex review F9).
- `_candidate_targets(vault: LoadedVault, repository: Repository, lo_id: str, topic: str, reads: _Provenance, covered: set[str], statements: set[str]) -> list[CueTarget]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 419) — The holding pen's candidates on this LO (``misconception_candidates`` and the open causal hypotheses projected into it, grouped by their recurrence key, Slice 2 T1): a class seen more than once is a recurrence group, a single one a hypothesis; open by its lifecycle (Codex review…
- `_gap_targets(vault: LoadedVault, repository: Repository, lo_ids: Sequence[str], covered: set[str]) -> list[CueTarget]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 453) — Named learner-text gaps on these LOs, not undone (the learner's "not what I meant" hides a gap from cue targets, D37); a gap naming a misconception or a holding-pen candidate already a target is that target, not a second one.
- `_facet_title(vault: LoadedVault, facet_id: str) -> tuple[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 498)
- `_facet_targets(vault: LoadedVault, repository: Repository, lo_ids: Sequence[str], failure: Callable[[str | None], float | None]) -> list[CueTarget]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 505) — Facets of these LOs with a demonstrated capability ("a new application").
- `_claim_targets(vault: LoadedVault, repository: Repository, extraction_id: str, lo_ids: Sequence[str], failure: Callable[[str | None], float | None]) -> list[CueTarget]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 567) — A claim needing an independent check on a facet of these LOs: a target for "try this step first" only (§6.1, G42; Codex review F9).
- `_scope(repository: Repository, extraction_id: str, guard: Protection) -> Scope` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 687)
- `_lo_neighbourhood(vault: LoadedVault, lo_ids: Sequence[str]) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 722) — The target's LOs and their confusables (concept-graph reading).
- `_own_contrasts(repository: Repository, extraction_id: str) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 760) — The passages this judge's own links gave a contrast role before.
- `_on_target(keys: Sequence[tuple[str, str]], extraction_id: str, span_los: SpanLearningObjects, los: set[str]) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 768) — ``keys`` on the open extraction and the target's LOs, once each, in order.
- `_judge_envelope(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> SharedDailyEnvelope` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 929)
- `_calls_cap(vault: LoadedVault) -> int` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 936)
- `_daily_calls_cap(vault: LoadedVault) -> int` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 948)
- `_window_start(clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 952) — Now (UTC) less 24 hours, in the receipts' own format (``datetime.isoformat`` with ``+00:00``), so it compares as text.
- `_daily_admission(vault: LoadedVault, repository: Repository, extraction_id: str, *, clock: Clock | None) -> Callable[[SpendEstimate], None]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 979) — ``PaidCalls``'s admission of each judge attempt (a retry included): refused before it is sent once the source's calls in the last 24 hours reach ``cues.max_calls_per_source_per_day``, whatever route (the subscription too) and whatever open.
- `_recovered(repository: Repository, route: Any, prompt: str, validate: Callable[[CueJudgeResult], CueJudgeResult]) -> CueJudgeResult | None` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1010) — A judged answer's own paid output (checkpoint, else receipt), when the ledger answered "cached" but the links were never written.
- `_link_id(extraction_id: str, target: CueTarget, span_id: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1030)
- `_settled(repository: Repository, targets: Sequence[CueTarget], extraction_id: str) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1143) — Targets whose state was judged and whose picks are links already.
- `_judge_readiness(vault: LoadedVault, client: Any | None) -> tuple[Any, Any | None, str | None, str | None]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1171) — The judge's route and client, resolved before anything is paid for (Codex review F2): ``(route, client, status, reason)``; a status means no target is retrieved deeply or judged.
- `_metered_room(vault: LoadedVault, repository: Repository, route: Any, *, clock: Clock | None) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1192) — Whether a metered judge has any of today's allowance left (a subscription judge is never refused for money).
- `_spend_plan(vault: LoadedVault, repository: Repository, route: Any, pending: Sequence[tuple[CueTarget, Shortlist]], *, clock: Clock | None, extraction_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1202) — The dry run's read-only spend plan (Codex review F13): the resolved route and its cost basis, the judge calls a run would send (each target's prompt as the dry run's keyword shortlist builds it, so the real one may differ in its passages), the query embeddings retrieval may buy,…
- `_because(target: CueTarget) -> str` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1393)
- `_note(relation: str, target: CueTarget, passage_topic: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1399)
- `_earlier(vault: LoadedVault, repository: Repository, target: CueTarget, cache: dict[str, dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1413) — "Open · what you worked on" for a discovered cue (spec §6.1, UX §4.4; Codex review F12): the cited answer the target was read from (the question as it was answered, the answer in the learner's words), the learner's own words a gap was named from, and the target's statement in Le…
- `_guide_p_open(_cue: Mapping[str, Any]) -> tuple[float, str]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1510) — A Guide cue's target is an active error on its LO: open by its lifecycle.
- `_public(cue: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/passage_cues.py), line 1697)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]] — imports `discover`; statically calls `discover`
- [[Reference/Modules/learnloop/source_retrieval/role_labeller|learnloop.source_retrieval.role_labeller]] — imports `protection`; statically calls `protection`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `discovery_enabled`, `merged_cues`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `module`; statically calls `discover`, `discovery_budget`, `discovery_enabled`, `find_discovered`, `merged_cues`, `protection`, `try_first_enabled`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `spend_envelopes`; calls `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `held_out_material`; calls `held_out_material`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `module`; calls `gaps`, `reversals`
- [[Reference/Modules/learnloop/db/stores/reader_cue_links|learnloop.db.stores.reader_cue_links]] — imports `module`; calls `insert_link`, `judged_left_ids`, `links_for_extraction`, `links_with_roles`, `shown_impressions`, `tables_present`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `episode_hypothesis_set`, `episode_posterior`; calls `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `pending_jobs`, `pipeline_enabled`; calls `pending_jobs`, `pipeline_enabled`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `demonstrated_capabilities_for_facet`; calls `demonstrated_capabilities_for_facet`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`
- [[Reference/Modules/learnloop/placement/predictor|learnloop.placement.predictor]] — imports `active_predictor`; calls `active_predictor`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `ListwiseTask`, `judge_listwise`, `route_skip`, `task_output_tokens`; calls `ListwiseTask`, `judge_listwise`, `route_skip`, `task_output_tokens`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `receipt_answer`, `resolve_client`, `transport_problem`; calls `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `receipt_answer`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/reader/reader_cues|learnloop.reader.reader_cues]] — imports `module`; calls `cue_candidates`, `cue_density`, `cues_enabled`, `current_verdicts`, `earlier_work`, `off_sources`, `one_per_viewport`, `render_note`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`; calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/reader/reader_sessions|learnloop.reader.reader_sessions]] — imports `SESSION_GAP`, `module`; calls `claims_from_judgments`, `on_demand_enabled`, `positive_filter_enabled`, `propose_roles`, `sessions_for_source`, `split_sessions`
- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `session_summary`, `source_learning_objects`; calls `session_summary`, `source_learning_objects`
- [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]] — imports `RoleProposal`, `module`, `tolerate_malformed_roles`; calls `tolerate_malformed_roles`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `Scope`, `block_roles`, `effective_eligibility`, `extraction_scope`, `model_reader_withheld`, `teaching_exclusions`; calls `Scope`, `block_roles`, `effective_eligibility`, `extraction_scope`, `model_reader_withheld`, `teaching_exclusions`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `correction_lists`, `expanded_learning_objects`, `source_object_lists`; calls `correction_lists`, `expanded_learning_objects`, `source_object_lists`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `ROLES`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `QUERY_EMBEDDING_CAPS`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `NEXT_STEP_ROLES`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `search_spans`; calls `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SharedDailyEnvelope`, `midnight`; calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/text_canon|learnloop.text_canon]] — imports `canonical`; calls `canonical`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `decimal`, `hashlib`, `json`, `math`, `os`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]], [[Reference/Modules/learnloop/source_retrieval/role_labeller|learnloop.source_retrieval.role_labeller]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]], [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/passage_cue_fakes.py](../../../../../../tests/passage_cue_fakes.py) — direct import
- [tests/test_passage_links.py](../../../../../../tests/test_passage_links.py) — direct import
  - `test_a_lost_link_write_is_recovered_from_the_paid_answer_without_paying_again`
  - `test_a_metered_judge_without_a_price_is_skipped_and_with_a_cap_is_held_to_it`
  - `test_a_pick_whose_quote_is_not_its_passages_words_is_dropped_never_repaired`
  - `test_a_second_open_pays_nothing_and_a_new_statement_recomputes_only_its_own_links`
  - `test_a_source_teaching_none_of_the_targets_los_has_no_targets`
  - `test_codex_on_the_subscription_is_never_refused_by_the_metered_cap`
  - `test_contrast_and_correction_lists_join_the_fusion_and_the_manifest`
  - `test_discovery_switched_off_does_nothing`
  - `test_every_discovered_link_has_a_ledger_verdict_and_a_verified_quote`
  - `test_one_source_open_makes_at_most_max_calls_per_source_open`
  - `test_roles_are_kept_with_confidence_judge_and_ledger_and_never_exclude`
  - `test_targets_are_the_open_sources_states_each_with_its_statement_and_p_open`
  - `test_the_dry_run_lists_targets_and_shortlists_and_calls_and_writes_nothing`
  - `test_the_judges_role_vocabulary_is_rw4es`
  - `test_the_shortlist_never_carries_a_solution_or_held_out_passage`
  - `test_with_the_judge_stubbed_to_none_no_discovered_cue_appears`
- [tests/test_reader_cue_holdout.py](../../../../../../tests/test_reader_cue_holdout.py) — direct import
  - `test_a_held_out_cue_is_not_shown_and_carries_its_seed_and_propensity_guide_cues_never_are`
  - `test_the_draw_withholds_about_the_rate_and_rate_zero_withholds_nothing`
  - `test_the_seed_reproduces_the_draw_and_the_propensity_is_the_draws_probability`
- [tests/test_reader_cue_value.py](../../../../../../tests/test_reader_cue_value.py) — direct import
  - `test_a_new_application_is_ordered_by_the_predictors_p_failure_on_its_passages_lo`
  - `test_a_target_seen_this_visit_ranks_after_targets_not_yet_seen_and_placement_alone_never_demotes`
- [tests/test_reader_rw3b_fix_round4.py](../../../../../../tests/test_reader_rw3b_fix_round4.py) — direct import
  - `test_a_logged_impression_stores_the_exact_propensity`
  - `test_the_draw_and_its_propensity_use_one_unrounded_rate`
- [tests/test_reader_rw3b_fix_round5.py](../../../../../../tests/test_reader_rw3b_fix_round5.py) — direct import
  - `test_a_tap_after_the_plan_changed_keeps_the_seen_plans_density_and_propensity`
  - `test_failed_requests_count_against_the_daily_cap_and_the_cli_run_is_held_to_it`
  - `test_new_open_ids_a_reload_and_a_restart_never_exceed_the_sources_daily_calls`
  - `test_the_daily_cap_refuses_a_retry_that_would_pass_it`
  - `test_the_dry_run_names_the_daily_cap`
- [tests/test_reader_rw3b_fix_round6.py](../../../../../../tests/test_reader_rw3b_fix_round6.py) — direct import
  - `test_a_receipt_24_hours_and_a_second_old_drops_out_of_the_window`
- [tests/test_reader_rw3b_protection.py](../../../../../../tests/test_reader_rw3b_protection.py) — direct import
  - `test_a_reading_held_out_whole_is_never_searched`
  - `test_every_discovered_template_and_rendered_line_is_free_of_trait_and_verdict_words`
- [tests/test_reader_rw3b_review_fixes.py](../../../../../../tests/test_reader_rw3b_review_fixes.py) — direct import
  - `test_a_candidate_a_durable_misconception_already_states_is_not_a_second_target`
  - `test_a_claim_needing_an_independent_check_is_a_try_first_target`
  - `test_a_metered_judge_request_reserves_once_under_the_cue_envelope`
  - `test_a_misconceptions_cited_answer_is_its_newest_source_events_attempt`
  - `test_a_retry_is_a_second_request_and_reported_apart_from_judgments`
  - `test_failed_requests_count_against_the_per_open_cap`
  - `test_holding_pen_candidates_and_recurrence_groups_are_targets`
  - `test_nothing_is_retrieved_deeply_for_a_judge_that_cannot_run`
  - `test_open_shows_the_cited_answer_and_the_learners_own_words`
  - `test_retrievals_metered_requests_reserve_under_the_cue_envelope`
  - `test_the_dry_run_names_settled_targets_and_carries_a_spend_plan`
  - `test_the_plan_says_when_background_work_can_still_name_a_target`
- [tests/test_reader_try_first.py](../../../../../../tests/test_reader_try_first.py) — direct import
  - `test_a_shown_skill_never_gets_a_try_first_cue`
  - `test_pressing_try_first_is_a_learner_pick_that_opens_the_next_step_at_that_line`
  - `test_try_first_is_kept_only_on_a_worked_example_for_an_open_target`
- [tests/test_roles_judges.py](../../../../../../tests/test_roles_judges.py) — direct import
  - `test_a_missing_or_malformed_roles_field_never_fails_the_cue_judges_links`
  - `test_rw3b_contrast_list_a_confident_contrast_the_judge_may_not_be_shown_never_blocks_the_low_one`
  - `test_rw3b_contrast_list_takes_a_low_confidence_proposal_only_when_none_better_is_on_target`
  - `test_rw3b_prefers_contrast_and_counterexample_passages_for_distinction_cues`
  - `test_the_cue_judges_roles_become_proposals_for_every_judged_passage`
  - `test_the_judges_result_schemas_are_the_base_trees`
  - `test_two_judges_agreeing_on_a_passages_role_make_one_proposal_with_two_versions`
  - `test_with_on_demand_off_the_cue_judge_writes_nothing_and_asks_the_same`
- [tests/test_roles_switch_off.py](../../../../../../tests/test_roles_switch_off.py) — direct import
- [tests/test_roles_switch_off_legacy_parity.py](../../../../../../tests/test_roles_switch_off_legacy_parity.py) — direct import
- [tests/test_rw4d_rw3b_composition.py](../../../../../../tests/test_rw4d_rw3b_composition.py) — direct import
  - `test_every_passage_rw4ds_predicate_withholds_is_one_the_cues_never_surface`

## Modification guidance

- Make changes here when the responsibility remains passage cues within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/passage_cues.py](../../../../../../src/learnloop/source_retrieval/passage_cues.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
