# Chat frontend C1a, narrowed: one structural rule for text ("land narrow, then fix source")

**Stage:** `mcp-c1a-narrow`, branch `mcp/c1-read-context` (worktree `learnanything-mcp`), base `34527fa13`.
**Code:** `3bdc89da7`. Main is `a9356f986` (mvp-0.24); it was not merged here (convergence with R2a's
`LearnerStateCardV1` happens at landing).
**Spec:** [spec_mcp_frontend_c1.md](../specs/spec_mcp_frontend_c1.md) §4.6, §4.7 rule 1 and §4.8 (new).
**Earlier records:** [mcp-c1a.md](mcp-c1a.md), [mcp-c1a-codex-review.md](mcp-c1a-codex-review.md),
[mcp-c1a-f4-codex-review.md](mcp-c1a-f4-codex-review.md). This stage's gate supersedes theirs.

## Why: the owner's decision (2026-10-14)

The F4 fix chased provenance from the output back to the answers behind each text. It was reopened five times.
The last verify (Codex job `20261014-205718-WNjtvF247`, on `0b53313ef`) reopened F1 and F2 again:

- a **snapshot diagnosis** reads the whole-vault export without recording what it opened. It copied a key
  from a pinned answer's grading, whose joint grader had been shown an unpinned answer, into its summary and
  into a misconception. The guard saw a closure of `{current}`.
- a **missing C4 receipt** (written outside the grading transaction, failures swallowed) reads as "shown
  nothing" (Q14).
- a **generated topic's title**, read from the exported graph, was written as prose in a summary. Its
  **literal id** was put in a misconception statement.

Output-side matching cannot replace input provenance. Of the three options put to the owner (a threat model;
record input provenance at write time; narrow the C1a output), the owner chose **"Land narrow, then fix
source"**. C1a lands now with a narrow `learning_context` that is safe by construction. A later desktop stage
records diagnosis inputs at write time and unlocks the prose.

## The rule

A text leaves LearnLoop only when it is:

- **(a) authored vault text**: a topic's name or id that the learner or an authored vault file wrote, or the
  question as graded (the pinned contract's prompt);
- **(b) the learner's own answer on a pinned attempt**, through the existing answer guard: its protection,
  exactly one pinned contract on its own item, and no key its item is known to have had;
- **(c) a derived text with a recorded, complete write-time provenance whose inputs are all safe**
  (`WriteProvenance`). This is the hook for the follow-up stage. **No producer writes a record yet.**

Everything else is withheld with one fixed reason: **`Held back until LearnLoop records what this was written
from`**. An entry whose own answer is protected names that reason instead (for example, "a check waiting in
the app").

## What chat shows now, and what it holds back

| Tool | Shown | Held back |
|---|---|---|
| `learning_context` | Every entry, with its id, status, severity, evidence and episode counts, dates, labels, held state and repairs tried; the learner's own pinned answers; the question as graded; authored topic names and ids; a gap's words when they *are* a pinned answer (shown as the attempt records it); retention risks; recurrence groups (keyed keys) | Misconception statements and corrections; candidate statements; hypothesis statements (open hypotheses, a trace's diagnosis hypotheses); recurrence-group statements; diagnosis summaries (the status shows); what a gap was matched to; a gap's words when they are a question the learner asked; every generated topic's name (a fixed label), id (an opaque keyed alias, accepted back as a named id, never matched by a topic search) and seeded question |
| `today` | Blocks, lanes, minutes, item counts, reading sections, authored topic names; a computed why naming authored topics only | A generated topic's name (the label); a why that names a generated topic (the computed why embeds the titles it was built with) or that a model wrote |
| `progress` | Goals, standing counts, authored topic names and ids, retention risks | A generated topic's name and id, in goal topics, the assumed list and retention risks (the label and alias) |
| `status`, `library`, `find_sources` | Unchanged | Unchanged (no topic names or model prose in their output) |

## What changed

| Piece | Where |
|---|---|
| **`TextGuard`**, the one renderer: `_authored` (a), `answer` (b), `derived` (c). Each builds its own release type (`AuthoredText`, `AnswerText`, `RecordedText`); a test pins that nothing else builds them | `src/learnloop/learner_context.py` |
| **Removed (unused under the rule):** `AnswerTextGuard` and its provenance graph: `Origin`, the Tarjan `closure`, the `_local_*` nodes (grading, graded, diagnosis, hypothesis, episode, event, shown, misconception, candidate, gap, title), the `_map` links, `_belief`, `_named_topics`, `_id_list`, `_cited_answers`, `PROVENANCE_MISSING`, `PROVENANCE_UNKNOWN`, `REVISION_UNKNOWN_ASKED`, `ANSWER_DERIVED_FIELDS`, `NON_ANSWER_FIELDS`. `learner_context.py` went from 2030 to 1751 lines. There is no second authority | same |
| **The hook (c):** `WriteProvenance(complete, answers, items, topics)`; `ProvenanceSource(connection, kind, record_id)`; `DERIVED_KINDS` (misconception, misconception_correction, candidate, hypothesis, diagnosis, learner_text_gap, learning_object, practice_item); `no_write_provenance`, the only source in use | same |
| **Classification:** `RELEASED_BY` (each content field and the rules that may release it) and `STRUCTURAL_FIELDS` (ids, codes, times, fixed notes) cover every text field of the output schema | same |
| **Q12:** `today` and `progress` name topics through the same guard | `src/learnloop/remote/views.py` |
| **Q13:** recurrence-group keys (`rg_<HMAC>`) and generated-topic aliases (`lo_withheld_<HMAC>`) are HMAC-SHA256 under a per-vault key, `.learnloop/mcp/alias-key` (0600, beside the endpoint token). `learnloop mcp serve` makes the key; it is never printed and token rotation leaves it alone. With no key, aliases use a key for this process | `src/learnloop/remote/endpoint_token.py`, `runtime.py`, `src/learnloop_mcp/cli.py` |
| The server passes the vault's alias key. The tool description and the instructions say that held-back wording is held back, so the host does not guess it | `src/learnloop_mcp/server.py` |
| Tests: 28 new cases. The F4 rounds 3–5 reproductions were kept and re-asserted as "no leak, held back", and the closure-internal checks were dropped. The shared builders moved to `tests/mcp_world.py` | `tests/test_mcp_c1a_narrow.py`, `test_mcp_c1a_review.py`, `test_mcp_tools.py`, `mcp_world.py` |

## Fail first

The new tests were written first and run against `34527fa13`. **28 of 28 failed.** The check was repeated
before the gate with the whole `34527fa13` `src/` and `migrations/` (from `git archive`) placed first on the
import path (`-o pythonpath=` overrides the project's `pythonpath = ["src"]`). Again **28 of 28 failed**. Each
reproduction failed on its leak assertion:

| Reproduction (the last verify, plus Q12 and Q13) | Leaked on `34527fa13` | Now |
|---|---|---|
| A snapshot diagnosis copies a key from a pinned peer's grading (its C4 history named the unpinned answer) into `analysis_md` and into a cause on the pinned answer's event; a misconception, a candidate, a hypothesis and its group are drawn from that cause | `LEGACY KEY 8841 …` in the misconception, candidate, hypothesis and group statements | All held back; entries, counts and status kept; the pinned answer and its question shown |
| No C4 receipt for the peer: its joint grader's cause, a misconception from it, and a diagnosis shown the peer | the key in the misconception and the summary | Held back; the peer's own answer shown |
| A generated title read from the snapshot graph, written as prose in a summary | `legacy key 8841 a row swap negates the volume` | Held back |
| A generated topic's literal id in a misconception statement (the summary is generic) | `lo_ltg_legacy_key_8841_…` | Held back |
| The withheld topic's alias was `sha256(id)`, which a client can recompute from a guessed title | `lo_withheld_fe7367…` | Keyed alias |
| A recurrence group key `rg:` + SHA-256 of the root statement (Q13) | `rg:9d7bb5a32cb53596eb64` | `rg_<HMAC>` |
| `today` and `progress` on a generated topic (Q12) | `Ltg Legacy Key 8841 …` as a block topic, in the why and in retention risks | Label, alias, why held back |

The other 21 cases test the new contract: the release types, the hook, the keyed aliases, the alias-key file
and the schema classification. They also failed before, because the names did not exist.

## The schema test

`test_every_text_field_is_authored_an_answer_or_withheld_without_a_record`:

- reads the advertised `learning_context` output schema and checks that every text field is in exactly one of
  `RELEASED_BY` or `STRUCTURAL_FIELDS`;
- plants derived text everywhere: a belief with a correction, a diagnosis with its summary, a gap matched to a
  belief, a gap drawn from the pinned answer, and a generated topic with a seeded, answered item in every
  section;
- **without records**: no field holds a `RecordedText`, no planted text appears anywhere, every (a) and (b)
  field is released at least once by its own type, and every topic field stands in at least once;
- **with a safe record for every derived text**: every field that (c) may release is released, as
  `RecordedText` only;
- structural fields never hold released text.

`test_a_recorded_provenance_releases_nothing_unless_complete_and_safe` covers 11 cases: incomplete, empty, an
unpinned answer, a protected answer, an unknown answer, a protected item, a generated topic, an unknown topic,
text that states a key, a malformed record, and a source that raises.

## Manual run (backup-API copies, read-only, no model, no network)

Run on `fixtures-local/c1a-manual/{linear_algebra,probability}`, the backup-API copies
(`learnloop.db.copies.copy_tree_with_databases`) the earlier rounds made and migrated. Every `*_API_KEY` was
blanked and every model client refused. `learning_context` (30 traces), `views.today` and `views.progress`
were called directly. "Before" is the `34527fa13` source tree on the import path; "after" is `3bdc89da7`. The
databases' SHA-256 values were unchanged afterwards. Outputs are in `fixtures-local/c1a-narrow-manual/`.

| Vault | Before (`34527fa13`) | After (narrow) |
|---|---|---|
| linear_algebra (plan off, no goals; 3 hypotheses, 1 misconception, 1 candidate, 0 diagnoses, 0 gaps, 0 generated topics, 11 C4 receipts in the database) | 30 traces: 12 answers and 13 stems shown (15 exam, 1 cold check, 1 probe, 1 states the key); 2 open hypotheses, **1 statement shown**, 1 withheld as a diagnostic check; 7 retention risks; 21 topics in scope, 0 aliases | **Identical except one field:** the shown hypothesis statement (a learner-state cause on "Compute with Complex Numbers") is now `Held back until LearnLoop records what this was written from` |
| probability (plan off, no goals; nothing derived on record) | 2 traces, 2 answers and 2 stems shown; 1 retention risk; 18 topics | **Identical** |

A deep diff of the two JSON outputs on linear_algebra shows exactly two changed fields, that entry's
`statement` and `statement_note`. All `today` and `progress` outputs are identical: neither copy has a plan,
a goal or a generated topic, so every retention-risk topic is an authored name. Timings, before and after:
`learning_context` 517 and 492 ms (linear_algebra), 48 and 46 ms (probability); `progress` 188 and 186 ms,
141 and 134 ms. **Paid calls: 0; cost: $0.**

## The follow-up stage: "diagnosis input provenance" (desktop scope, unlocks the prose)

Queued after method-explicit lands (spec §4.8). Each writer records exactly what it read, in the transaction
that writes the text, as the `WriteProvenance` the read model already checks:

1. **Diagnoses** record the attempts, files and snapshot entries they read. The snapshot export's opened files
   map back to attempts, items and topics; an export the diagnoser cannot account for makes the record
   incomplete. The normalizer, gap reader and drafter carry the union of their inputs' records forward (a
   closed record).
2. **C4 receipts** are written inside the grading transaction (Q14).
3. **Regrades keep event-id lineage** (Q9).
4. **`question_events` record the item contract** a question was asked about (Q10).
5. **What of an item a writer saw.** (c) filters a released text against the answer keys of the items and
   topics its record names, not against rubrics or reference solutions. A writer that read either must
   record it, and the check must filter against it (or refuse the record), before a producer is switched on.

When those land, a `ProvenanceSource` reading them replaces `no_write_provenance`. The read model needs no
other change, and the schema test already checks the released path.

## Decisions taken (defaults)

- **A question the learner asked is (c), not (b).** The owner's rule names "the learner's own pinned
  answer". A tutor question can quote what the learner was shown after a reveal, and a Reader question can
  quote an exam paper the learner was reading. Its words are held back until Q10's record exists (Q15).
- **A gap drawn from an answer shows the answer as the attempt records it** (`practice_attempts`), not the
  excerpt the gap row stored. That is (b) by construction.
- **Protection names itself first.** An entry whose own answer or item is protected shows that reason ("a check
  waiting in the app", "a diagnostic check") rather than the generic one, with or without a record.
- **A seeded question is (c).** An item on a generated topic was seeded from the learner's question by the
  question-promotion path, so its prompt is drafted text: its stem is held back, and the learner's own answer
  to it shows.
- **A plan block's why** is shown only when it was computed (`why_kind == "computed"`) and none of the block's
  topics, displaced items included, is generated. No producer on this branch writes a model why. R2b's
  router (on main) will, and its why is held back.
- **The alias key** lives beside the endpoint token, is made by `serve`, and is never printed or rotated with
  the token, so aliases stay stable for the hosts that hold them. Attaching and viewing never write it; the
  `test_attach_and_every_view_write_nothing` file check holds.
- `context_version` stays `learner_context_v1`: C1a has not shipped.

## Open questions for the owner

- **Q15 (new): learner questions.** Should a tutor question asked *during* a pinned attempt count as (b),
  through the same answer guard? It would show more of the gaps section now. The default taken is no: (c)
  until Q10's record exists, because a question can quote a revealed solution or exam text the key filter does
  not know.
- **Q16 (new): R2a convergence.** The card's reader is the router's model, not a chat host. When the card
  gathers its sections from this module, should it take the narrow text rule too? It would lose the hypothesis
  statements the router reads. Or should it keep its own G5? Recommended: keep the card's G5, share the
  predicates and the protection, and make the text rule a parameter of the read model.
- **Q11 is moot.** No generated name is shown, so there is no subject cascade. **Q12 and Q13 are closed.**
  Q9, Q10 and Q14 move to the follow-up stage. Q1 to Q8 are unchanged.

## Gate

Run on `3bdc89da7`, with TMPDIR set to the worktree's `fixtures-local/tmp`. Logs are
`fixtures-local/c1a-narrow-fullsuite.log` and `c1a-narrow-durability.log`, each headed by the commit it ran
on. The record commit after it changes docs and removes two unused test imports; the C1a tests were rerun
on it.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **21 kept, 0 broken** |
| `git diff --check 34527fa13..3bdc89da7` | clean |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10763 passed**, 0 failed, 17 warnings (10:44; 16:25 including the wait for the lock). Round 5 had 10737: plus the 28 new cases, minus the 2 review cases moved. The 17th warning is a timing-dependent `PytestUnhandledThreadExceptionWarning` from the reading-sweep thread in `test_success_head`, unrelated to this change |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10663 deselected (3:15) |
| The C1a tests alone (`test_mcp_c1a_narrow`, `test_mcp_c1a_review`, `test_mcp_tools`, `test_mcp_runtime`, `test_mcp_http`, `test_mcp_cli`) | **124 passed** (round 5 had 98: 28 new narrow cases; the review file lost 2 cases, its schema and renderer tests, which moved to the narrow file and were rewritten) |
| DB reference generate/validate, CLI help snapshot, config references | not applicable: no schema, CLI or config change |
| npm / cargo | not applicable: nothing under `apps/learnloop-tauri` changed |
| Paid calls | none ($0) |
