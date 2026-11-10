"""Why x and not y: the one reader over decision records and the rows older than them (ADR-017, refactor B9).

``reader.answer`` is the read every surface uses: ``learnloop why``, the sidecar's read-only ``why.get``, and the
views ``learnloop router trace`` and ``learnloop trace-evidence``. ``reconstructed`` answers decisions made before
their records existed, from the rows they left, and labels what it reconstructs.
"""
