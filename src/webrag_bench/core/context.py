"""State shared by the episodes of one worker: plan, archive, cached indexes, and —
for plans with signed provenance — the party keys and the public-key registry."""

from __future__ import annotations

from functools import lru_cache

from webrag_bench.core.plan import Plan
from webrag_bench.core.tasks import Task
from webrag_bench.corpus import WarcReplay, is_adversarial_url
from webrag_bench.index import Doc, Index, build_embedder, build_index
from webrag_bench.provenance import KeyRegistry, PartyKey
from webrag_bench.readers import get_reader
from webrag_bench.servers.signing import origin_of, party_keys


class RunContext:
    def __init__(
        self, plan: Plan, replay: WarcReplay, freeze_fingerprint: str, bench_version: str
    ) -> None:
        self.plan = plan
        self.replay = replay
        self.freeze_fingerprint = freeze_fingerprint
        self.bench_version = bench_version
        self.tasks: dict[str, Task] = {t.id: t for t in plan.tasks()}
        self.embedder = build_embedder(plan.config.embedder)
        self.index = lru_cache(maxsize=64)(self._build_index)
        self.party_keys: dict[str, PartyKey] = {}
        self.registry = KeyRegistry()
        prov = plan.config.provenance
        if prov is not None:
            origins = [origin_of(u) for u in replay.urls()]
            self.party_keys, self.registry = party_keys([*origins, prov.peer_party], prov.key_seed)

    def _build_index(self, family: str, reader_name: str, index_name: str) -> Index:
        """Index of the corpus as published for one attack family.

        Benign pages plus the adversarial pages of `family` only; indexed through the
        episode's reader, as a real pipeline would.
        """
        read = get_reader(reader_name)
        docs = [
            Doc(url, read(self.replay.get(url)))
            for url in self.replay.urls()
            if not is_adversarial_url(url) or is_adversarial_url(url, family)
        ]
        return build_index(index_name, docs, self.embedder, self.plan.config.hybrid_alpha)
