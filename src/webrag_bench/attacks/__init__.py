"""Attack families: templates, canaries and insertion points."""

from webrag_bench.attacks.canary import canary
from webrag_bench.attacks.templates import INSERTION_POINTS, Template, inject, load_templates

__all__ = ["INSERTION_POINTS", "Template", "canary", "inject", "load_templates"]
