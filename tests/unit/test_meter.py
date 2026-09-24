from webrag_bench.provenance import PartyKey, ProvenanceMeter, canonical_json, issue, verify
from webrag_bench.servers.signing import party_keys


def test_meter_accumulates_sign_and_verify_costs():
    key = PartyKey.derive("site.test", "s")
    _, registry = party_keys(["site.test"], "s")
    meter = ProvenanceMeter()
    att = meter.timed_sign(issue, key, "http.get", {"url": "u"}, "page")
    problems = meter.timed_verify(verify, att, registry, output="page")
    assert problems == []
    summary = meter.summary()
    assert summary["attestations"] == 1
    assert summary["meta_bytes"] == len(canonical_json(att.to_dict()))
    assert summary["sign_ms"] > 0
    assert summary["verify_ms"] > 0
