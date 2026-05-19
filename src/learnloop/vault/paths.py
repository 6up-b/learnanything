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


def find_vault_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "learnloop.toml").exists():
            return candidate
    raise FileNotFoundError(f"No learnloop.toml found above {start}")
