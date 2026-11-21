"""Read an explicit artifact and write a structure-only report to explicit scratch."""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
from typing import Iterator

from learnloop.notebook_authoring.marimo_adapter import inspect_structure


class OutputPathError(ValueError):
    """The requested output cannot be confined without overwriting existing data."""


@contextmanager
def _output_directory(path: Path) -> Iterator[int]:
    if '..' in path.parts:
        raise OutputPathError('parent traversal is not allowed')
    absolute = path.absolute()
    # Reports may contain private code facts; a checkout is never an output store.
    if any((parent / '.git').is_file() or (parent / '.git/HEAD').is_file()
           for parent in (absolute, *absolute.parents)):
        raise OutputPathError('choose an output directory outside the checkout')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory = os.open(absolute.anchor, flags)
    try:
        for part in absolute.parts[1:]:
            try:
                child = os.open(part, flags, dir_fd=directory)
            except FileNotFoundError:
                os.mkdir(part, mode=0o700, dir_fd=directory)
                child = os.open(part, flags, dir_fd=directory)
            os.close(directory)
            directory = child
        # Both names must be unused before either report is written. Exclusive
        # creation below also rejects a symlink/hardlink planted after this check.
        for name in ('structure.json', 'structure.txt'):
            try:
                os.stat(name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise OutputPathError(f'{name} already exists; choose a fresh output directory')
        yield directory
    except OSError as exc:
        raise OutputPathError('output must use real directories and unused report files, without symlinks') from exc
    finally:
        os.close(directory)


def check_structure(path: Path, out: Path) -> tuple[dict, str]:
    """Return the report and summary; the source is never imported or modified."""
    if path.suffix != '.py':
        raise ValueError('The structure checker takes a marimo .py notebook.')
    report = inspect_structure(path.read_text(encoding='utf-8'))
    report.update(scope='structure', structure_status='failed' if report['findings'] else 'passed',
                  review_status='incomplete', accepted=False, execution_performed=False,
                  review_layers_performed=[])
    summary = (f"Structure only: {report['structure_status']}; {len(report['cells'])} cells; "
               f"{len(report['findings'])} findings.\n"
               'Review incomplete: no execution, no review layers; not acceptance.\n')
    with _output_directory(out) as directory:
        for name, contents in (('structure.json', json.dumps(report, indent=2) + '\n'), ('structure.txt', summary)):
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                handle.write(contents)
    return report, summary
