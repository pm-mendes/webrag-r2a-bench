"""Mechanical stage oracles. No human or LLM judgement is involved here."""

from webrag_bench.oracles.stages import Stages, decide_stages
from webrag_bench.oracles.utility import decide_utility

__all__ = ["Stages", "decide_stages", "decide_utility"]
