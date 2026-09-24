"""Generator construction from its plan declaration."""

from __future__ import annotations

from webrag_bench.config import GeneratorConfig
from webrag_bench.generators.base import Generator
from webrag_bench.generators.openai_compatible import OpenAICompatibleGenerator
from webrag_bench.generators.stub import StubGenerator


def build_generator(config: GeneratorConfig, seed: int | None = None) -> Generator:
    if config.type == "stub":
        return StubGenerator(config.name, config.version_id)
    assert config.base_url  # enforced by GeneratorConfig
    return OpenAICompatibleGenerator(
        config.name, config.version_id, config.base_url, config.key_env,
        temperature=config.temperature, max_tokens=config.max_tokens, seed=seed,
    )
