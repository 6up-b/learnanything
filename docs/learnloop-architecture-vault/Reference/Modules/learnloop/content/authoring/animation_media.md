---
title: "learnloop.content.authoring.animation_media"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/animation_media.py"
source_paths:
  - "src/learnloop/content/authoring/animation_media.py"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.animation_media module"
  - "src/learnloop/content/authoring/animation_media.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.animation_media`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.animation_media` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: mp4 post-processing for stored concept animations.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/animation_media.py](../../../../../../../src/learnloop/content/authoring/animation_media.py) |
| Source lines | 210 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `589b35df8e5e3ce56849cbdab681c6bc12737419` |
| Commit timestamp | `2026-09-03T10:26:28-07:00` |

## Public API

- `probe_duration_seconds(data: bytes) -> float | None` ([source](../../../../../../../src/learnloop/content/authoring/animation_media.py), line 22) — Container duration in seconds via PyAV; ``None`` on any failure.
- `top_level_atoms(data: bytes) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/animation_media.py), line 39) — Names of the top-level ISO-BMFF boxes in file order (ftyp, moov, mdat, ...).
- `is_faststart(data: bytes) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/animation_media.py), line 57) — True when ``moov`` precedes ``mdat``: the file plays without seeking back.
- `remux_faststart(data: bytes) -> bytes` ([source](../../../../../../../src/learnloop/content/authoring/animation_media.py), line 64) — Stream-copy remux so ``moov`` precedes ``mdat``.
- `concat_clips(clips: Sequence[bytes], *, fps: int | None=None) -> bytes` ([source](../../../../../../../src/learnloop/content/authoring/animation_media.py), line 138) — Join mp4 clips into one faststart H.264 file by re-encoding.

## Internal implementation anchors

- `_video_stream(container: Any) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/animation_media.py), line 114)
- `_stream_fps(stream: Any, fallback: int) -> int` ([source](../../../../../../../src/learnloop/content/authoring/animation_media.py), line 118)
- `_stream_extent_seconds(stream: Any, container: Any, av: Any) -> float | None` ([source](../../../../../../../src/learnloop/content/authoring/animation_media.py), line 127) — How long the video track itself runs (not the container, which an audio track or a start offset can stretch).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `concat_clips`, `probe_duration_seconds`, `remux_faststart`; statically calls `concat_clips`, `probe_duration_seconds`, `remux_faststart`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `fractions`, `io`, `logging`, `pathlib`, `shutil`, `struct`, `tempfile`, `typing`
- Third party: `av`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_animation_media.py](../../../../../../../tests/test_animation_media.py) — direct import
  - `test_concat_clips_defaults_to_the_source_frame_rate`
  - `test_concat_clips_joins_in_order_as_one_faststart_stream`
  - `test_concat_clips_rebases_offset_clips_and_ignores_longer_audio_tracks`
  - `test_concat_single_clip_is_just_a_faststart_remux`
  - `test_probe_duration_is_none_for_garbage`
  - `test_probe_duration_is_none_without_pyav`
  - `test_probe_duration_reads_container_duration`
  - `test_remux_faststart_moves_moov_first_and_keeps_duration`
  - `test_remux_faststart_passes_garbage_through`
  - `test_remux_faststart_returns_input_when_pyav_missing`
  - `test_top_level_atoms_and_faststart_detection`
- [tests/test_concept_animation_service.py](../../../../../../../tests/test_concept_animation_service.py) — direct import
  - `test_generate_stores_faststart_remuxed_bytes_and_hashes_them`
  - `test_generate_video_model_path_stores_stitched_clip_and_provenance`

## Modification guidance

- Change animation media policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/animation_media.py](../../../../../../../src/learnloop/content/authoring/animation_media.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
