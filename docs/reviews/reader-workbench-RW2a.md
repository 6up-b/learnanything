# Reader workbench RW2a: the resumable scratchpad (stage `reader-rw2a`)

Branch `reader/rw2a` (worktree `learnanything-merge4`), base `main` at
`9cdaefb9e` (`mvp-0.27`, one eligibility decision; migration head 206). Spec:
`docs/specs/spec_reader_workbench_v1.md` §13 row RW2a and what it cites (§5.1,
§5.4 source visibility and what an attempt records, §5.6, §5.7's
`workbench_sessions` and `workbench_steps`, §5.8, §5.9 successor none and
`workbench.enabled`), §3.4, §12, §14 (G5's source-visible and no-help rows,
G6, G10, G11, G32, G58), §16, §20 (§20.9). Presentation:
`docs/specs/ux_reader_workbench_v1.md` §1, §3.4, §4.0, §4.12, §5 (RW2a parts),
W5, W8, W15, §10 S1/S2/S6/S7/S13.

## 0. Plan (written before the code)

**Scope.** RW2a only. No model call of its own (the one paid call it starts is
the existing `import_exercises` job, on its own route and caps). No grading,
regrade, replay or eligibility rule changes.

**Migration 207** (`migrations/207_workbench.sql`):
- `workbench_sessions` (WORKFLOW): §5.7's columns, every CHECK'd column with
  all its values (`import_status` none|pending|bound|failed; `origin`
  reader|practice|plan; `entry` all eight; `status` open|submitted|abandoned;
  `help_style` let_me_struggle|balanced|guide_me, null until RW2b).
- `workbench_steps` (RAW_LEDGER, append-only by trigger): `id`, `session_id`,
  `ordinal`, `kind` step|stuck, `body_md`, `supersedes_id`, `deleted`,
  `client_idempotency_key` (unique per session), `created_at`. An edit is a
  new row superseding the head of its chain; a delete is a tombstone row; an
  undo is a row superseding the tombstone.
- `db/table_roles.py` classifies both; `fixtures/migration_head_206` becomes
  `migration_head_207` (backup-API copy, only 207 applied, rollback journal),
  its README and every hard-coded path; the DB reference scripts regenerate.

**Backend** (`learnloop/reader/workbench.py`, functional core + shell;
`db/stores/workbench.py`; `learnloop_sidecar/handlers/workbench.py`):
- RPCs `workbench.open`, `.get`, `.save_step`, `.set_book`, `.leave`,
  `.abandon`, `.reopen`, `.refresh_import`, `.bind`, `.retry_import`,
  `.submit`, `.session_for_attempt`, `.for_item`, `.for_source` (the last is
  the read RW6a's recap will call: open and abandoned sessions on a source,
  with `unfinished` past `open_session_days`). Desktop only (D20), pinned off
  the phone.
- Opening at once (S2): `open` with a selection stores the verbatim stem and
  enqueues the existing exercise import itself (the same code
  `reader.import_exercise` runs); `refresh_import` binds when the job lands
  (one item binds; several ask which part; none or a failed job is
  `failed`, steps kept, "try again").
- Book visibility by entry (S7, D9): a pure default per `entry`; flipping
  before the first step is free; the first step with the book open, or opening
  it afterwards, stamps when the book first counted.
- Submit composes through the ordinary `submit_attempt` path (one shared
  implementation, `entry_surface = 'desktop_reader_workbench'` for the Reader,
  `'desktop_practice_workbench'` for the practice screen and plan): the
  answer is the live `step` rows in order (stuck rows and tombstones
  excluded); `hints_used` is 1 when the book counted (plus the existing
  tutor-question fold, then the existing cap); the attempt type is the one the
  answer box picks (`stuck_attempt_type`); an empty work list with an empty
  stuck box is the existing empty stuck answer. The submit therefore asks
  `serve_eligibility.decide` exactly as every submit does
  (`attempts._resolve_attempt_target`); a refusal keeps the session open and
  the steps.
- Every lifecycle change logs a salience-only `reader_action_invoked` with a
  payload `event` (no new event kind, no new reveal kind).

**Kill switch** `workbench.enabled` (default true) and `workbench.open_session_days`
(30): modelled defaults, out of the decision-only template. Off: every
workbench RPC refuses `workbench_disabled` and writes nothing, the config DTO
carries no `workbench` key, and no screen shows an entry. Every
`DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry recomputed with the "no scoring,
scheduling, projection or serving change" note. No successor (§5.9), unless
the mapping check (§5.4 against `resolve_attempt_activity_policy`) finds one.

**Frontend** (`screens/workbench/`): the pure step model and record line, the
write queue hook (saved · just now / not saved yet — retrying / sidecar
unreachable), the `Workbench` component (header, problem, book line, steps in
`LiveMarkdownEditor`, I'm stuck, Submit with its record line, Leave for now,
`⋯` Abandon, abandoned · reopen), the half-window split (resizable, remembered,
min 480 px) and the stacked layout under 1,040 px with *show in the book*; the
Reader's entries (*work through this* on a selection and on an imported
exercise, `✎` resume beside the passage, the rail's unfinished problems),
book hidden over the source pane (W8), collapse back to reading at the passage;
App: a Reader workbench submit goes to feedback and Esc/b return to the
problem read-only, then to reading; the practice screen's remembered *Work in
steps* and *resume your steps* on the practice card. Chords checked against
`LiveMarkdownEditor`.

**Tests, fail-first:** a backend file per gate group (lifecycle, source
visible record, eligibility composition, grader blindness, switch-off
identity, migration and roles) and vitest files for the step model, the
workbench component and the screens (Reader working posture, practice
screen, back from feedback, switch-off DOM identity against a snapshot taken
on the base code).
