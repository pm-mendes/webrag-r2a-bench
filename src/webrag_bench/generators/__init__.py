"""Generators: the model that reads the context and emits tool calls.

Each generator is declared in the plan with a frozen `version_id`. For a remote
generator, the model id returned by the provider is compared with the declared id on
EVERY call; a mismatch is recorded on the episode as `model-substitution`. Nothing is
substituted silently.
"""

from webrag_bench.generators.base import Generator, Response
from webrag_bench.generators.openai_compatible import OpenAICompatibleGenerator
from webrag_bench.generators.registry import build_generator
from webrag_bench.generators.stub import StubGenerator

__all__ = ["Generator", "OpenAICompatibleGenerator", "Response", "StubGenerator", "build_generator"]
