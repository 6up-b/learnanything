# LearnAnything / LearnLoop

Local adaptive learning vault for anything you want to learn. LearnLoop keeps
your knowledge as editable Markdown/YAML in a vault and stores derived learning
state (attempts, FSRS scheduling, mastery, scheduler explanations, proposals) in
a local SQLite database. The full MVP target is defined in `spec_mvp.md`.

CLI and the Textual TUI are both first-class surfaces. Neither owns scheduling,
grading, mastery, or proposal logic; both call the same service layer. Codex is
optional: every local workflow (review, attempt, self-grade) works without it,
and Codex-backed authoring/grading is auditable and never writes files directly.

## Install

```powershell
python -m pip install -e .[dev]
learnloop --help
```

Requires Python 3.12+.

## Quick start (local, no Codex)

```powershell
# 1. Create a vault
learnloop init my-vault

# 2. Add a subject and some source material
learnloop add-subject linear-algebra "Linear Algebra" --vault my-vault
learnloop add-note linear-algebra note_svd "SVD overview" --body "Notes..." --vault my-vault

# 3. Check vault health (and safely sync derived SQL state)
learnloop doctor --fix-state --vault my-vault

# 4. See the due queue with one-line "why" reasons
learnloop review --vault my-vault

# 5. Attempt an item with non-interactive self-grade
learnloop attempt pi_svd_define_001 --answer "..." \
  --criterion-points correctness=3 --confidence 4 --vault my-vault

# 6. Inspect anything by id, or explain a scheduled item
learnloop show <id> --vault my-vault
learnloop why pi_svd_define_001 --vault my-vault

# 7. Launch the Textual today loop
learnloop today --vault my-vault
```

Learning Objects and Practice Items are normally created through Codex authoring
proposals, but you can also import a validated `AuthoringProposal` file:

```powershell
learnloop propose --file proposal.json --vault my-vault
learnloop proposals --vault my-vault
learnloop accept <patch_id> --vault my-vault   # applies YAML + change/content events
learnloop reject <patch_id> --vault my-vault
```

## MVP commands

| Command | Purpose |
|---|---|
| `init` | Create a vault and default config |
| `add-subject` | Add a subject view and metadata |
| `add-note` | Register note/source material |
| `propose` | Generate/import authoring proposals |
| `proposals` | List proposal batches and item decisions |
| `accept` / `reject` | Apply or decline proposal items |
| `attempt` | Run an attempt (Codex grade with self-grade fallback) |
| `review` | Print the due queue with why summaries |
| `why` | Explain a queued or recently queued item |
| `show` | Universal inspector for any vault or SQL id |
| `doctor` | Validate vault health (`--json`, `--fix-state`) |
| `today` | Launch the Textual today loop |

Scriptable commands support stable `--json` output for golden tests.

## How it works

- **Storage** — Markdown/YAML vault + `state.sqlite`. Migrations live in
  `migrations/`; YAML reads/writes go through `vault/`.
- **Scheduler** — deterministic priority over `forgetting_risk` (FSRS-6),
  `active_goal`, `recent_error`, and probe-only `probe_eig`.
- **Mastery** — logit-space Kalman update per Learning Object.
- **Surprise & follow-ups** — predictive/Bayesian surprise per attempt; strong
  negative surprise can insert a follow-up Practice Item from the same pool.
- **Probe-EIG** — new active-goal LOs enter a locked-hypothesis probe phase that
  contributes expected information gain to ranking.
- **Codex** — typed `AuthoringProposal` / `GradingProposal` objects are
  validated and persisted with `agent_runs` lineage before any content mutation.

## Development

```powershell
python -m pip install -e .[dev]
python -m pytest -q
python -m compileall -q src tests
```

The automated test suite is the source of truth for the acceptance gates in
`PLANS.md`; deterministic tests run without Codex, Textual terminals, or
network access.
