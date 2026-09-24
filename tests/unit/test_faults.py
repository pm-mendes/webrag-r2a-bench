import pytest

from webrag_bench.core.episode import draw_faulty
from webrag_bench.core.plan import Cell
from webrag_bench.provenance import extract, issue, verify
from webrag_bench.servers.signing import Faults, party_keys


@pytest.fixture
def setup():
    keys, registry = party_keys(["site.test", "other.test"], "s")
    att = issue(keys["site.test"], "http.get", {"url": "u"}, "page")
    return registry, att


def test_healthy_party_is_untouched(setup):
    registry, att = setup
    result = Faults(frozenset({"other.test"}), "corrupt").apply("site.test", "page", att)
    assert verify(extract(result), registry, output="page") == []


def test_missing_attestation(setup):
    _, att = setup
    result = Faults(frozenset({"site.test"}), "missing").apply("site.test", "page", att)
    assert extract(result) is None
    assert result.content[0].text == "page"


@pytest.mark.parametrize("mode", ["corrupt", "unknown-key"])
def test_invalid_signatures_are_caught(setup, mode):
    registry, att = setup
    result = Faults(frozenset({"site.test"}), mode).apply("site.test", "page", att)
    assert verify(extract(result), registry, output="page") == [
        "invalid signature for issuer 'site.test'"
    ]


def test_faulty_draw_is_deterministic_and_sized():
    parties = [f"p{i}" for i in range(8)]
    assert draw_faulty(parties, 0.0, 1) == frozenset()
    assert len(draw_faulty(parties, 0.25, 1)) == 2
    assert draw_faulty(parties, 0.5, 7) == draw_faulty(parties, 0.5, 7)
    assert draw_faulty(parties, 1.0, 1) == frozenset(parties)


def test_fault_rate_enters_the_key_only_when_nonzero():
    base = Cell("m", "T", "F1", "none", "g", "bm25", "r", 0, "on")
    assert "|fault=" not in base.key()
    assert Cell("m", "T", "F1", "none", "g", "bm25", "r", 0, "on", 0.5).key().endswith("|fault=0.5")
