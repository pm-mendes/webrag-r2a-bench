"""Freeze fingerprint and campaign entry gate.

The SHA-256 fingerprint covers the plan, templates, tasks, defenses, judge and the
WARC archive. It is written into every record: a template that changes after the
freeze changes the fingerprint, and the change is visible in the data.
"""

from webrag_bench.freeze.fingerprint import fingerprint
from webrag_bench.freeze.gate import IncompleteFreeze, blocking_markers, require_complete_freeze

__all__ = ["IncompleteFreeze", "blocking_markers", "fingerprint", "require_complete_freeze"]
