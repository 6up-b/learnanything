"""Read an activity and its fixed companion filenames without importing any artifact."""
from __future__ import annotations

import os
from pathlib import Path
import stat

from learnloop.notebook_authoring.check import write_reports
from learnloop.notebook_authoring.contract import inspect_contract
from learnloop.notebook_authoring.manifest import check_manifest, static_manifest
from learnloop.notebook_authoring.scratch import directory_fd


def _read(directory: int, name: str, *, optional=False) -> bytes | None:
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=directory)
    except FileNotFoundError:
        if optional:
            return None
        raise
    with os.fdopen(fd, 'rb') as handle:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError(f'Expected a regular artifact file for {name}.')
        return handle.read()


def check_contract(path: Path, out: Path):
    if path.name != 'activity.py':
        raise ValueError('Contract checks take activity.py with its sibling key.py when needed.')
    with directory_fd(path.parent) as directory:
        activity = _read(directory, 'activity.py')
        key = _read(directory, 'key.py', optional=True)
        supplied = _read(directory, 'manifest.json', optional=True)
    report = inspect_contract(activity.decode('utf-8'), key.decode('utf-8') if key is not None else None)
    manifest = static_manifest(report, activity, key)
    if supplied is not None:
        report['findings'].extend(check_manifest(manifest, supplied))
    status = 'failed' if report['findings'] else 'passed'
    report.update(scope='contract', contract_status=status, accepted=False, execution_performed=False,
                  review_layers_performed=[], review_status='incomplete')
    summary = (f"Static contract {status}; {len(report['findings'])} findings.\n"
               "Review incomplete: no execution, no review layers; not acceptance.\n")
    write_reports(out, 'contract', report, summary, manifest=manifest)
    return report, summary
