# Follow-up generate and serve, FG1 (`followup/fg1-generate-serve`, base `9780ca3baf`)

Built from `docs/specs/spec_followup_generate_serve_v1.md`, every section except §7's marks table and report (FG1c). Successor
`mvp-0.45` after `mvp-0.44`, kill switch `followup.generate_and_serve`, migration 241 (recheck the number against main at landing).

## What exists now

| Spec | Where |
|---|---|
| §5 item 1, §3.1: the durable workflow | `followup_serve/workflow.py` (a leaf), `db/stores/followup_serve.py`, `attempts/post_attempt.py::_open_followup_workflow`, `diagnosis/split/jobs.py::_workflow_diagnosis_ended`, the fourth worker slot in `learnloop_sidecar/post_attempt_worker.py` |
| §4.2: single use | `followup_serve/identity.py`, the doors listed below, `generated_probe_items`, `generated_probe_burns` |
| §4.1, §5.1: authoring to the pinned offer | `followup_run/authoring.py`, `followup_run/admission.py`, `accept_probe_offer(candidate_id=, followup_workflow_id=)` |
| §4.3: entry and needs | `probe_episodes.enter_episode` enqueues; `followup_run/jobs.py::_run_entry`, `_run_need`, `_run_factor_need` |
| §5: the router | `daily_plan/router_chooser.py::FollowupGate`, `router/plan_log.py::build_followup_decision`, `followup_run/router.py`, `router_decision_bindings`, `router/outcomes.py::_follow_binding`, `daily_plan/engine.py::_place_followup_probes` |
| §6: the desktop | `followup_run/serving.py`, `learnloop_sidecar/handlers/followup.py`, `screens/feedback/FollowupPanel.tsx`, `screens/FeedbackScreen.tsx` |
| §10: the phone | The phone's own miss opens no workflow; `device_deferred_count` counts a pending probe, so the existing "waiting for the desktop" line says so |
| §9 | All five specs carry a dated "Amended by FG1" note |

**Package split.** The import contract forbids a new cycle, so `learnloop.followup_serve` is a leaf (switches, workflow record,
queue writes, identity) that domain packages may read, and `learnloop.followup_run` is the composition, imported only by the
sidecar. A small `attempt_followup_grade` lives in `diagnosis/followups.py`, so `attempts` keeps its one existing edge.

## The doors of §4.2

| Door | What it does now |
|---|---|
| Queue, direct-by-id | `routine_withhold_reason` (`generated_probe_closed`, `generated_probe_reserved`), `sidecar/serving.py::refuse_generated_probe_door` on `open_queue_item`, `get_practice_item`, `get_probe_contract` |
| Plan pool | Same gates through `pool_admission`; `reconcile` displaces a standing planned item that is retired or was served elsewhere. A probe served here and unanswered reopens as the same administration |
| `find_practice` | Unchanged (diagnostic modes excluded); a stale pick meets the serve door |
| Teacher | `_probe_headers` leaves out every generated probe |
| AD | `admitted_new_material_ids` subtracts them |
| Exams | `exam_pool` candidates leave them out |
| Phone | The door refuses any serve with a request origin; submit's rejection is unchanged |
| MCP | Unchanged: read-only, no question text |
| Follow-up tasks | `_insert_pending_followups` drops them, overriding the repair-journey allowance |
| Rebuild replay | `replay_learning_object` keeps ledger-closed items inactive; nothing generates during rebuild |
| `state_sync` | `practice_item_activatable` takes the ledger |
| Check once | `admission_reason(requested=True)` refuses, so standing assignments too |
| Remint | `generated_probe_single_use` |

## Where the build departs from the spec's words, and why

1. **Constraint refusals arrive after generation on the plan path.** The plan's constraint engine reads an item, and at decision
   time none exists (§5 item 2 requires the decision first). The orchestrator's refusals (a learner's "Not now", pending machine
   checks, an episode conflict) still come before any spend. A plan constraint is checked when a waiting probe reaches its
   boundary. Smallest alternative to a full check: a learning-object-level constraint read before generation, if a dry run shows
   the wasted generations matter.
2. **Automated adversarial review does not run.** §4.1 runs it "only if its cost fits the wait". It would double the physical
   calls per probe, so the default is off and the admission receipt says `adversarial_review: not_run`. Real latency is for the
   owner's run on a copy, which can change this.
3. **A pinned follow-up presentation has no TTL.** §4.2 says abandonment closes it. A wait can outlast the 240-minute default, and
   an expiry after a burn would make the one submission fail.
4. **The routine session caps don't refuse a workflow's probe** (`get_probe_contract`). The router already decided, and otherwise a
   burned probe would serve as ordinary practice with its measurement lost.
5. **No-plan misses get no `no_intervention` draw**, the spec's stated default in §5.1.
6. **A block's follow-up uses the attempt that closed it**, when that attempt is a miss. §3.1 says completion "releases
   eligibility" without saying which of a block's misses it picks. The earlier misses keep the block's own diagnosis path.
7. **Teach-back misses stay on the predecessor's path.** Their door has its own screen, with no pending and skip UI (§3.1's rule).
8. **New vaults store no `auto_generate_on_entry = true`.** §4.3 says "new vaults get `true`", and the successor's effective setting
   gives every vault at the tag exactly that. The decision-only template holds no `[probe.generation]` section (the spec's line 286 is
   the older full template), and adding one would make the switch's off state differ from mvp-0.44 on a new vault. The review's own
   rule (§10) wins: off, the stored value applies, and new and old vaults alike store none.
9. **The feedback's "Show anyway" is the only hold exit from the plain surface.** The inspector can still read an attempt's raw
   record if the learner digs there; it records its own exposure, as today, and §6.0's flag for the probe's independence comes from
   the workflow only. If the owner wants the inspector held too, it reads the same `is_holding`.
10. **A pre-FG1 generated probe keeps its old rules.** The identity is registered as an item is written; an upgrade does not
    backfill items already in a vault, whose diagnostic mode still makes them single use by the attempt rule. Open question below.

### Gates that could not be made fully observational

None on this lane. Checked: the follow-up value check never runs while the workflow owns the attempt (insertion is withheld before
it); the probe contract's value refusal is reached only with no committed presentation, and a workflow's probe always has one;
`decide_probe` and repair-class divergence are logged on the row (`detail_json.observational`), and with shared repair classes that
fact goes on the router's card.

## Measured with fakes

Physical authoring calls per probe: 1 (`test_a_miss_with_two_rivals_generates_one_pinned_probe`). A transport failure: 2, the first
and the one retry the workflow admits, then the failure line (`MAX_GENERATION_ATTEMPTS`). A hard refusal, a `no_intervention` draw
or unreadable protection: 0. Every physical call is admitted and recorded through `runtime.spend.metered` under
`owner_kind=followup_generation`, one owner per job, so the owner's run on a copy reads calls and cost per probe from
`model_call` receipts. Real latency and vault growth are for that run: no paid call was made in this stage.

## Open questions for the owner

1. Backfill the single-use identity onto `pi_gen_*` items already in the owner's vaults, or leave them on the older attempt rule?
2. Q4 (§12) stands at its default: the answer is held until the probe is answered and released on a wait.
3. Run on a copy: real latency and calls per probe, whether the adversarial review fits the wait, and vault growth.
