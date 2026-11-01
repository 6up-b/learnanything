# Reader follow-ups Nov 1b

Stage `reader-followups-nov1b`, branch `reader/followups-nov1b` (base `0d607bdfe9`, worktree `learnanything-merge2`).

This stage builds four queued follow-ups. Each one has fail-first tests named after the finding it closes.

- **No migration, no successor, no config key. Kill switches unchanged.**
- One new module constant, `figures/labels.py:MIN_SEGMENT_WORDS`, a `keep` structural bound. It is registered in `params/parameter_registry.py`.
- Nothing here changes persisted meaning (scoring, scheduling, projections, serving).
- No paid or live model call was made. Every model in the tests is a fake. The adapter test runs the real `openai` SDK and httpx over httpcore with a fake network backend, so no socket is opened.
- No Python ran outside pytest except `lint-imports`.
- Cost: $0.

## 1. RW5d §9b.4: the free-text label rule (P2b ruling R2)

P2b ruling R2 (`reader-rw5d-p2b-manim.md`): "The §9b.4 rule that model-written free text (narration, title, what it
shows, assumptions) must not read like a check label is not built in this stage. Queued as a follow-up to land before
the owner gives the Manim opt-in."

### What changed

**The label module** (`src/learnloop/figures/labels.py`, new) holds the code-owned label constants:

- the grammar figure's and the abstention badges;
- the sketch badges;
- the Manim badges and its closing check line;
- the check lines' lead, `CHECKS_LEAD = "checked by LearnLoop:"`.

These constants moved out of `figures/service.py` and `figures/rich.py`. Both modules re-export them under their old names, as the same objects, so every caller and test is unchanged.

**Matching.** `label_like(text)` matches structurally, built from those constants and not from a hand-written phrase list:

- **Label phrases.** Each label as written, plus each segment of three or more words that states a check, plus its positive form (*not checked against the book* → *checked against the book*). The full set is `LABEL_PHRASES`.
- **Check words in badge form.** The check words are `CHECK_LABEL_WORDS = ("checked", store.VERIFIED_RW5C)`. Badge forms are:
  - bracketed: *(checked)*, *[verified]*;
  - their own `·` segment or the whole text: *Verified*;
  - a lead: *Checked: …*;
  - naming LearnLoop: *verified by LearnLoop*, *LearnLoop has checked*.
- **Check-mark glyphs** (`CHECK_GLYPHS`: ✓ ✔ ☑ ✅ 🗸).
- **Normalization.** Matching ignores case, Unicode compatibility forms (NFKC) and separator variants (`·•∙⋅`).
- **Not matched:** ordinary prose, such as *check that the area is 1*, *we verified the identity by expanding*, *the box is checked*, *the sum is verified.*

**Fields read.** The rule reads:

- what each figure shows (`demonstrates`) and its assumptions, on the spec, the sketch, the V3 quick figure and the rich brief;
- the tier reason (`why_this_tier`, and V2's `why_not_spec`);
- a Manim figure's `title` and `narration_md`.

Labels drawn inside the frame (series, readout and probe labels) are not this rule's fields. Identifiers stay with the sketch tier's `impersonates`.

**On a hit, the repair call.** `label_problems` writes the problem in code's words, naming the field and the phrase. It becomes the author's (or rich author's) problem for its one existing repair call. The check runs before the spec, sketch or brief is parsed (`figures/service.py:_free_text`, called right after the status is read). No new call is added: this is the existing second attempt.

**Still violating after the repair**, each tier keeps its existing path:

- **Spec or sketch:** shown without that text (`_without_label_text`, `labels.strip_json`). `demonstrates` is emptied, a label-like assumption is dropped, and every other field is kept.
- **Tier reason:** replaced with `REASON_WITHHELD`, in code's words, on the `figure_tier` receipt.
- **Rich brief:** stripped the same way before the rich job receives it.
- **Manim title or narration:** `manim_figure.parse_figure` raises `ManimFigureError`, so the rich job's second attempt fails like any invalid answer. The figure is stored `failed` and never shown. This applies to the render-repair path too. The narration is the video's transcript, its text alternative, so a cut transcript is not shown.

### Tests

`tests/test_figure_label_wording.py`, 37 tests.

**The matcher**, tested without the rest of the pipeline:

- 15 label-like texts are matched, and 10 ordinary or empty texts are not (`REASON_WITHHELD` included);
- the vocabulary comes from the code-owned constants, and the tiers' constants are the module's own objects;
- desktop parity: `FIGURE_FRAME`, `SKETCH_FRAME` and `RICH_FRAME` carry the same strings, and every badge-slot or check-line string the desktop draws reads as a label;
- problems are in code's words;
- `strip_json` leaves out only label-like text.

**The tiers** (`test_r2_…`):

- spec demonstrates: repair with code's words;
- spec still label-like: shown without the text, stored without it;
- ordinary prose costs no repair call;
- sketch still label-like: shown without the text;
- a label-like `why_not_spec`: repaired, then left out of the receipt;
- rich brief and `why_this_tier`: repaired, then left out (the brief reaches the rich author stripped);
- Manim title: repair with code's words;
- Manim narration still label-like: refused, stored failed, no render.

**Fail-first evidence.** The behaviour tests were run with the rule switched off: a pytest plugin replaced `label_problems` with "no problems" and `strip_json` with identity. **7 of 8 `r2_` tests failed.** The one that passed is the ordinary-prose test, which is expected.

## 2. RW5d P2b R1: failed corrections from the durable rows

P2b ruling R1 (F14 remainder): "Queued follow-up: discover unresolved correction failures from durable figure/request
rows instead of the job window."

### What changed

- **New lookup.** `rich.rich_job_for_request(repository, request_id)` finds the newest `figure_rich` job of a figure request, over the whole queue. It uses `newest_ingest_job_by_payload`, as `rich_job_for_quick` already does.
- **`service.rich_pending`** now walks the window's jobs first, then the jobs of every stored failed rich correction for this source whose job is outside the window. A stored failed correction is a row that is `failed`, has a rich spec version, a `supersedes_id` and a `request_id`. Its job is found by the request id and must correct the same figure.
- **Same rules as before.** Both kinds of job go through the existing loop: input dedupe, a newer correction of the same figure speaks for it, `_failed_correction`'s still-newest check, the show-me switch and held-out passages.
- **Retry.** "Try again" (`rich_revision_retry`) already read the job by id over the whole queue.
- **`list_figures`** never read the window. The fuller line's job comes from `rich_job_for_quick`, which reads the whole queue. It is unchanged.
- **The window itself** (newest 500) still serves the pending and waiting lines, which are recent by nature.

### Tests

`tests/test_figure_rich_failed_correction_durable.py`, 4 tests. The window is aged out by filtering the job out of `rich_jobs`, which is what 500 newer rich jobs would do.

| Test | Before the fix |
|---|---|
| a failed correction outside the window still lists its line, with the same reason, job and retry | **failed** |
| a failed correction of a fuller version, outside the window | **failed** |
| a newer in-window correction still speaks for the figure | passed |
| a replaced failed correction lists nothing | passed |

## 3. Chat adapter R1: no environment proxy on the metered adapter

Reader follow-ups Nov 1 ruling R1 (F2 remainder): "Queued as a follow-up: bound nested TLS I/O, or set trust_env=False
on the metered adapter's client."

### What changed

- **The choice:** `trust_env=False`. LearnLoop has no proxy configuration key (`AIProviderConfig` has no proxy field, and neither does the config schema), so this follows the brief's rule: no explicit key, so drop the environment proxy.
- **Where.** `OpenAIChatProviderClient` builds the SDK's `DefaultHttpxClient(trust_env=False, verify=httpx.create_ssl_context(trust_env=True))`. This also covers `openrouter`, which subclasses it.
- **Effect:**
  - HTTPS_PROXY, HTTP_PROXY, ALL_PROXY and `.netrc` no longer route or authenticate a metered call. It connects straight to `base_url`, under the total deadline.
  - The certificate store still follows SSL_CERT_FILE or SSL_CERT_DIR (else certifi), exactly as before. Only the proxy is dropped.
- **Documentation:**
  - the comment at the construction site, including what to do if a proxy setting is ever added: pass it explicitly and bound nested TLS reads per `recv` first;
  - one paragraph in `docs/learnloop-architecture-vault/Workflows/Configure AI Providers.md`.
- **Unchanged:** `_DeadlineNetworkStream`. Its TLS-in-TLS path is now reachable only through an explicit proxy, and none exists.

### Tests

In `tests/test_chat_total_transport_deadline.py`:

- **`test_nov1_r1_an_environment_proxy_no_longer_routes_metered_calls[https-443 | http-80]`.** Every proxy variable is set to `http://proxy.invalid:3128`. The call must connect to `deadline.invalid` itself and answer.
  - Before the fix, both cases **failed** with `[('proxy.invalid', 3128)] == [('deadline.invalid', …)]`: the call went to the proxy.
  - The fake server now records each connection's `(host, port)`.
- **`test_nov1_r1_the_certificate_store_still_follows_the_environment`.** A missing SSL_CERT_FILE still fails construction, as it did before.

## 4. RW4d fresh path: a "no such passage" pin is not persisted

Reader follow-ups Nov 1, open item 3: "a fresh comparison stores every dropped pin, including one dropped as 'no such
passage' … the stored comparison is withheld whole (fail closed) for every later reader."

### What changed

- `source_retrieval/compare.py` stores `dropped_pins` without the `NO_SUCH_PASSAGE` pins, the same rule as the reuse path (Codex review F1).
- `result.dropped_pins` still carries the pin, so the current call is still refused whole (`comparison_withheld`).

### Tests

`tests/test_whole_comparison_reuse_provenance.py::test_nov1_open_item_3_a_fresh_comparisons_pin_naming_no_passage_is_not_persisted`:

- the fresh call with a pin naming no passage fails closed;
- the stored row has no "no such passage" pin;
- `withheld_comparisons` does not withhold it;
- a later call reuses it.

Before the fix it **failed**: the stored row had `"reason": "no such passage"`.

## Gate (this step; the full suite runs once, in the landing gate)

GATE_PLACEHOLDER

## Open items

1. **Owner (P2b item 2):** the Manim opt-in can now be given. R2's rule (item 1) is built and covers a Manim figure's title, narration, brief and tier reason.
2. **First-attempt figure lost.** A label hit on the first attempt spends the one repair call on the wording. If that repair then fails for another reason (numerics, a schema error), the first attempt's figure is not kept as a fallback, the same as for any other first-attempt problem. Keeping a stripped first attempt as a fallback (as the Manim pacing repair does) would be a small follow-up if it matters in practice.
3. **"matches the book" is not matched.** RW5c's eventual label is not a code-owned constant yet. When RW5c defines it in `figures/labels.py`, the rule covers it automatically. N-a's "never 'matches the book'" holds today because no code writes that label.
4. **The JS half.** `js_animation`'s `html`/`js` string literals (§9b.4) wait for the JS half (G-SM14).
