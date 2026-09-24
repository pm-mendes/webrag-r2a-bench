"""Generator construction from its plan declaration."""

from __future__ import annotations

from webrag_bench.config import GeneratorConfig
from webrag_bench.defenses import ToolCall
from webrag_bench.generators.base import Generator
from webrag_bench.generators.openai_compatible import OpenAICompatibleGenerator
from webrag_bench.generators.stub import StubGenerator


def build_generator(
    config: GeneratorConfig,
    seed: int | None = None,
    stub_benign_calls: dict[str, ToolCall] | None = None,
) -> Generator:
    """`stub_benign_calls` is only used by the stub generator (see StubGenerator)."""
    if config.type == "stub":
        return StubGenerator(config.name, config.version_id, stub_benign_calls)
    if not config.base_url:  # also enforced by GeneratorConfig
        raise ValueError(f"generator {config.name}: base_url is required")
    return OpenAICompatibleGenerator(
        config.name,
        config.version_id,
        config.base_url,
        config.key_env,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        seed=seed,
    )
