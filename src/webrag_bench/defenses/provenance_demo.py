"""Provenance-gated tool calls. DEMO policy, NOT the mechanism of paper Y.

Refuses every effectful call when any page in the context arrived without a valid
attestation. It exists to exercise the policy interface, the cost and the
degradation measures in dry runs. Two properties worth seeing in its results:

- it does not stop an injection hosted on a legitimate origin: that page is signed
  and verifies, since a signature attests origin, not harmlessness;
- under partial failure of signing parties it blocks benign work too, which is what
  the graceful-degradation measure captures.

The mechanism of paper Y (`pbd`) is defined in the manuscript and is not approximated
here.
"""

from __future__ import annotations

from webrag_bench.core.tasks import Task
from webrag_bench.defenses.base import DecisionContext, Defense, ToolCall
from webrag_bench.servers import EFFECTFUL_TOOLS


class ProvenanceGateDemo(Defense):
    name = "provenance-demo"
    requires_provenance = True

    def authorize(self, call: ToolCall, task: Task, context: DecisionContext) -> bool:
        if call.tool not in EFFECTFUL_TOOLS:
            return True
        return all(page["verified"] for page in context.pages)
