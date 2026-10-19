# Reader workbench RW1c: a tutor that looks things up (stage `reader-rw1c`)

Branch `reader/rw1c` (worktree `learnanything-merge4`), base `main` at
`fab576ac1` (RW2b + H3 landed; migration head 213). Spec:
`docs/specs/spec_reader_workbench_v1.md` §1's RW1c line, §4.6 in full, the
RW1c rows of §12 (signals) and §13 (phase table), §11's routes paragraph,
G48, G53, G59, the RW1c test lists (§14) and the §15 checkpoint metrics.
Presentation: `docs/specs/ux_reader_workbench_v1.md` §4.0 (pending as
*looking in your books…* then *writing…*), §4.2 (three answer modes, *another
way*, *that didn't help…*, the offers, abstention), W3, W14. Consumed, never
rebuilt: `spec_source_practice_and_probes_v1.md` §9.1 `find_sources` with its
intents (`explain`, `alternative`, `remediate`), §9.4 `compare_sources`,
§6.2 the deterministic practice request (S0), §10.3 the tutor's
`tool_requests` (S4), §6.5 `record_proposal_impressions`, `practice_availability`.
Friction notes read: RW1b §9 item 2 (reuse `find_sources(intent="alternative")`
with the inquiry's passages excluded; the three modes are the tutor's, not the
router's), RW4a §9 item 1 (the reader branch of `tutor_qa` takes an injected
span provider), RW6a §5 (nothing for RW1c).

## 0. Plan (written before the code)

**Which sources-spec phases are on `main`.** All of S0-S5 merged at
`5db645a33` (mvp-0.18/0.19): `find_sources` with intents and
`compare_sources` (S3), `tool_requests`, `run_source_tool`,
`record_source_offer_shown` and `practice_availability` (S4), the practice
request (S0), impressions with surface `reader`. So RW1c uses the real
interfaces; "absent" (G53) is `source_service.enabled = false`, where RW1c
falls back as §4.6 says (the base `find_sources` for the Reader's own
retrieval, `intent="explain"` with the shown passages excluded for *another
way* and *that didn't help*, "Practice this" as a plain `find_practice` on
the learner's question, no tool requests). RW5b is not on `main`, so "Make
this explorable" is absent; RW1b is, so "Try the next step first" is built.

**Scope (RW1c only).**
1. A Reader-context span provider (`source_retrieval/reader_tutor.py`) with
   its own query: the learner's question, the inquiry's ancestors and, when
   personalized, the open gaps on the passage's LOs; run through the sources
   service's `find_sources(verify=True)` under the server-derived Reader
   caller (`reading`; a bound workbench session's item gives
   `assisted_practice`; a cold administration `cold_attempt` and nothing).
   T6's rule 0 holds: when the verification route cannot run, nothing is
   retrieved or paid for and the tutor is today's. Retrieved spans join the
   tutor's context **after** the selection and its neighbours (the citation
   allowlist keeps them first), held to `tutor_qa.context_token_budget`;
   every passage passes the held-out filter and, item-bound, T6's exclusions
   and `span_leaks_expected`.
2. Three answer modes (`tutor/reader_modes.py`, a prompt and response-schema
   change used only while `reader_tutor.retrieval_enabled`): "From your
   books" (a verbatim excerpt quote-verified in code against its passage;
   dropped, with the answer falling back to mode 2, when its text is not in
   the passage, the passage is not one the tutor was given, it is the
   learner's own selection text, held out, or reproduces a bound item's
   answer), a grounded explanation (today's answer, now with retrieved
   passages), and a bridge to the learner's work (only with open gaps or
   recent workbench steps on the same LOs and the personalized toggle on).
3. Abstention: when verification ran and kept no passage, the answer opens
   with "Your books don't cover this directly — this is LearnLoop's model's
   explanation", the excerpt is dropped and no citation is shown as the
   books'.
4. *Another way* (`find_sources(intent="alternative")`, every passage shown in
   the inquiry excluded, labelled *from a different book* / *a worked example
   instead*) and *that didn't help…* (a branch whose text is a reader
   question; `find_sources(intent="remediate")` with the inquiry's named gaps
   as `target_hypotheses`), both as follow-ups through `reader.ask`.
5. Offers under the answer (`TutorOffers.tsx`, behind
   `reader_tutor.offers_enabled`): the sources spec's practice request and
   tool requests rendered as buttons; `find_practice` and `find_sources`
   lookups start when the answer lands and show nothing until pressed;
   impressions (`record_proposal_impressions`, surface `reader`) and span
   exposures (`record_source_offer_shown`) only on the press;
   `compare_sources` runs only when pressed; an empty lookup turns into the
   line *nothing in your practice or books fits this yet*; a failed one keeps
   its button and runs again on the press. Plus the Reader's own "Try the
   next step first" on a cited derivation or worked example in the open
   source (RW1b's next-step question at that line).
6. Report: a `tutor` row in `learnloop reader report` (answers by mode,
   abstentions, excerpts dropped, another-way and that-didn't-help rates and
   whether the next exchange resolved the inquiry, buttons shown and pressed
   by kind).

**Switches.** `reader_tutor.retrieval_enabled` (retrieval, modes,
abstention, another way, that didn't help) and `reader_tutor.offers_enabled`
(the buttons), both on (frictionless defaults); classified in the parameter
registry. With both off the tutor is byte-identical: pinned against goldens
recorded on the base tree before any RW1c code (pytest
`test_reader_tutor_switch_off.py` with `tests/fixtures/reader_tutor_switch_off.json`;
vitest `tutorSwitchOff.test.tsx` and its snapshot).

**No migration** (the spec says none): exchanges stay `question_events` with
the manifest; presses are `reader_action_invoked` events
(`tutor_offer_pressed`, with the `source_tool_calls` id when the tutor asked).
**No new route**: the tutor's existing route; the sources spec's functions
for theirs. **No new RPC**: `reader.ask` gains optional inputs; the offers use
the existing `find_practice`, `run_source_tool`,
`record_proposal_impressions` and `record_source_offer_shown`. Evidence:
retrieval is context and display; buttons are learner picks; nothing writes
evidence, mastery or grading inputs; a tutor answer's reveal handling is
today's.
