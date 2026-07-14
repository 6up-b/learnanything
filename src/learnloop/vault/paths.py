from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from learnloop.config import LearnLoopConfig


@dataclass(frozen=True)
class VaultPaths:
    root: Path
    config: LearnLoopConfig

    @property
    def config_path(self) -> Path:
        return self.root / "learnloop.toml"

    @property
    def sqlite_path(self) -> Path:
        return self.root / self.config.storage.sqlite_path

    @property
    def concepts_path(self) -> Path:
        return self.root / "concepts" / "concepts.yaml"

    @property
    def relations_path(self) -> Path:
        return self.root / "concepts" / "relations.yaml"

    @property
    def goals_path(self) -> Path:
        return self.root / "profile" / "goals.yaml"

    @property
    def error_types_path(self) -> Path:
        return self.root / "errors" / "error_types.yaml"

    @property
    def facets_path(self) -> Path:
        return self.root / "facets.yaml"

    def subject_dir(self, subject_id: str) -> Path:
        return self.root / "subjects" / subject_id

    def subject_markdown_path(self, subject_id: str) -> Path:
        return self.subject_dir(subject_id) / "subject.md"

    def subject_graph_path(self, subject_id: str) -> Path:
        return self.subject_dir(subject_id) / "concept-graph.yaml"

    def learning_object_path(self, subject_id: str, learning_object_id: str) -> Path:
        return self.subject_dir(subject_id) / "learning-objects" / f"{learning_object_id}.yaml"

    def practice_item_path(self, subject_id: str, practice_item_id: str) -> Path:
        return self.subject_dir(subject_id) / "practice-items" / f"{practice_item_id}.yaml"

    def note_path(self, subject_id: str, note_id: str) -> Path:
        return self.subject_dir(subject_id) / "notes" / f"{note_id}.md"

    # --- Vault-level source library (spec_source_ingestion_v2 §4.1) ----------
    # New canonical sources live at vault level, not under subjects/<id>/notes/.
    # Legacy subject-scoped source notes remain readable in place forever.

    @property
    def sources_dir(self) -> Path:
        return self.root / "sources"

    def source_dir(self, source_id: str) -> Path:
        return self.sources_dir / source_id

    def source_markdown_path(self, source_id: str) -> Path:
        # artifact/work metadata + current revision pointer
        return self.source_dir(source_id) / "source.md"

    def source_revision_path(self, source_id: str, revision_id: str) -> Path:
        # immutable normalized display rendering/frontmatter
        return self.source_dir(source_id) / "revisions" / f"{revision_id}.md"

    def canonical_source_raw_path(self, asset_hash: str) -> Path:
        # content-addressed fetched bytes (shareable by mirrors)
        return self.root / "canonical-sources" / "raw" / _sanitize_hash(asset_hash)

    def source_extraction_cache_dir(self, extraction_id: str) -> Path:
        # derived IR/assets/cache data
        return self.root / ".learnloop" / "source-cache" / "extractions" / extraction_id


def _sanitize_hash(asset_hash: str) -> str:
    # asset_hash carries a "sha256:" prefix; strip the scheme separator so it is
    # a safe path segment (content-addressed raw blob filename).
    return asset_hash.replace(":", "-")


def find_vault_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "learnloop.toml").exists():
            return candidate
    raise FileNotFoundError(f"No learnloop.toml found above {start}")
