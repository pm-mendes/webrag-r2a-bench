from webrag_bench.analysis.equality import equality_report


def _m(eid, family, digest, provenance="on", task="T01"):
    cell = {
        "subplan": "m",
        "task": task,
        "family": family,
        "defense": "none",
        "generator": "g",
        "index": "bm25",
        "reader": "r",
        "repetition": 0,
        "provenance": provenance,
        "fault_rate": 0.0,
    }
    return {"id_episode": eid, "cell": cell, "effects_digest": digest}


def test_pairs_equal_and_violations():
    measures = [
        _m("c1", "none", "A"),
        _m("a1", "F1", "A"),
        _m("a2", "F2", "B"),
        _m("c2", "none", "C", task="T02"),
        _m("a3", "F1", "C", task="T02"),
    ]
    r = equality_report(measures)
    assert (r.pairs, r.equal, r.rate) == (3, 2, 2 / 3)
    [violation] = r.violations
    assert violation["family"] == "F2"
    assert (violation["clean_episode"], violation["attacked_episode"]) == ("c1", "a2")
    assert violation["plan"]["task"] == "T01"
    assert "family" not in violation["plan"]


def test_filter_and_missing_reference():
    measures = [
        _m("c1", "none", "A", provenance="off"),
        _m("a1", "F1", "B", provenance="off"),
        _m("a2", "F1", "B", provenance="on"),
    ]
    assert equality_report(measures, where={"provenance": "on"}).pairs == 0
    assert equality_report(measures, where={"provenance": "off"}).pairs == 1
