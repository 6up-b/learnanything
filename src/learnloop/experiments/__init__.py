"""Research experiments: never part of production serving.

Code here evaluates candidate designs on backup copies of vaults
(``fixtures-local/``) and writes its own research artifacts. It may read
production modules; no production package imports it (import-linter contract
``experiments-stay-outside-production`` and ``tests/test_e0_isolation.py``).
The only entry point is the CLI (``learnloop experiments ...``), which imports
it lazily inside its commands.
"""
