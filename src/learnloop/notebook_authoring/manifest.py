"""The static coverage owed by a single revision, before any review round."""
from __future__ import annotations

from hashlib import sha256
import json

from learnloop.notebook_authoring.dependencies import notebook_pins


def _states(report):
    states = ['locked']
    for commit in report['declarations']['commits']:
        outcomes = ['correct', 'junk', 'free-text', *(f'mutant/{m}' for m in report['mutants'])]
        states.extend(f"{commit['id']}/{outcome}" for outcome in outcomes)
    return states


def static_manifest(report, activity: bytes, key: bytes | None):
    states = _states(report)
    cells = [c['name'] for c in report['cells']]
    return {
        'schema': 'notebook-static-manifest-v1',
        'activity_sha256': sha256(activity).hexdigest(),
        'key_sha256': sha256(key).hexdigest() if key is not None else None,
        'parser_version': report['parser_version'],
        'notebook_pins': notebook_pins(),
        'cells': cells, 'states': states,
        'coverage': [{'cell': cell, 'state': state, 'layer': layer, 'rounds': []}
                     for cell in cells for state in states for layer in ('layout', 'visual', 'teaching')],
        'interaction_coverage_owed': ['disclosures', 'tabs', 'extremes', 'pivotal-values', 'phone-width', 'palettes'],
        'screenshots': [], 'independent_oracles': [], 'execution_receipts': [],
        'review_status': 'incomplete', 'publication': 'unpublished', 'accepted': False,
    }


def check_manifest(expected: dict, supplied: bytes) -> list[dict]:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate manifest field')
            result[key] = value
        return result

    try:
        data = json.loads(supplied, object_pairs_hook=unique)
    except (ValueError, UnicodeError):
        data = None
    if not isinstance(data, dict):
        return [dict(kind='manifest_mismatch', cells=[], message='Expected a JSON object with unique fields.')]
    findings = []
    if set(data) != set(expected):
        findings.append(dict(kind='manifest_mismatch', cells=[], message='Static manifest fields differ.'))
    for field in expected.keys() & data.keys():
        # JSON distinguishes a claimed zero from a boolean false.
        if json.dumps(expected[field], sort_keys=True) == json.dumps(data[field], sort_keys=True):
            continue
        affected = []
        if field == 'coverage' and isinstance(data[field], list):
            present = {json.dumps(row, sort_keys=True) for row in data[field]}
            affected = sorted({r['cell'] for r in expected[field] if json.dumps(r, sort_keys=True) not in present})
        findings.append(dict(kind='manifest_mismatch', cells=affected, message=f'Stale or invalid manifest {field}.'))
    return sorted(findings, key=lambda f: f['message'])
