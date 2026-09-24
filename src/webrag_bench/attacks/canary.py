"""Canary tokens.

A canary is specific to one (family, task) pair. It appears only in the adversarial
page and in the arguments of the adversarial goal, so its presence downstream
(generator context, proposed call, server journal) is what the oracles test.
"""

from __future__ import annotations

import hashlib


def canary(family: str, task_id: str, salt: str) -> str:
    digest = hashlib.sha256(f"{salt}|{family}|{task_id}".encode()).hexdigest()
    return f"CNR{digest[:12].upper()}"
