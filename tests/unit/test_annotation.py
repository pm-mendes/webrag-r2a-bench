import json
from pathlib import Path

import pytest

from webrag_bench.annotation import BatchConfig, BatchError, build_batch, verify_batch
from webrag_bench.annotation import batch as batch_module

ITEM_KEYS = {"item_id", "request", "context", "response_text", "proposed_calls"}


def _fake_run(root: Path, n_per_cell: int = 10) -> None:
    run = root / "runs" / "src"
    run.mkdir(parents=True)
    with (run / "episodes.jsonl").open("w") as rec, (run / "transcripts.jsonl").open("w") as tr:
        i = 0
        for family in ("F1", "F2"):
            for defense in ("none", "secret-defense-x"):
                for _ in range(n_per_cell):
                    eid = f"ep-{i:04d}"
                    i += 1
                    rec.write(
                        json.dumps(
                            {
                                "id_episode": eid,
                                "famille_attaque": family,
                                "condition_defense": defense,
                                "generateur": {"nom": "secret-gen-y"},
                                "index_recherche": "bm25",
                                "lecteur": {"nom": "bs4-text"},
                                "tache": {"id": "T01", "type_action": "action-open"},
                                "erreurs": ["nesting-violated"] if i == 3 else [],
                            }
                        )
                        + "\n"
                    )
                    tr.write(
                        json.dumps(
                            {
                                "id_episode": eid,
                                "system_prompt": "s",
                                "request": f"request {i}",
                                "context": ["page"],
                                "response_text": "ok",
                                "proposed_calls": [],
                            }
                        )
                        + "\n"
                    )


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(batch_module, "ROOT", tmp_path)
    _fake_run(tmp_path)
    return tmp_path


def _config(name="b", **overrides):
    base = {
        "name": name,
        "status": "DEMO",
        "source_run": "src",
        "seed": 7,
        "strata": ["family", "defense_on"],
        "allocation": {"per_stratum": 4},
        "max_items": 100,
        "question": "q?",
        "labels": ["yes", "no"],
    }
    return BatchConfig.model_validate({**base, **overrides})


def _items(out: Path) -> list[dict]:
    return [json.loads(line) for line in (out / "items.jsonl").read_text().splitlines()]


def test_batch_is_stratified_and_blinded(root):
    out = build_batch(_config())
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["total_items"] == 16
    assert all(row["drawn"] == 4 for row in manifest["strata"])
    raw = (out / "items.jsonl").read_text()
    for item in _items(out):
        assert set(item) == ITEM_KEYS
    for secret in ("secret-defense-x", "secret-gen-y", "F1", "F2", "ep-"):
        assert secret not in raw


def test_batch_is_deterministic(root):
    a = build_batch(_config("a"))
    b = build_batch(_config("b"))
    assert (a / "key.jsonl").read_text() == (b / "key.jsonl").read_text()
    assert (a / "items.jsonl").read_text() == (b / "items.jsonl").read_text()


def test_nesting_violations_are_excluded(root):
    out = build_batch(_config(allocation={"per_stratum": 50}))
    keys = [json.loads(line)["id_episode"] for line in (out / "key.jsonl").read_text().splitlines()]
    assert "ep-0002" not in keys
    assert len(keys) == 39


def test_shortfall_is_reported_not_hidden(root):
    out = build_batch(_config(allocation={"per_stratum": 12}))
    rows = json.loads((out / "manifest.json").read_text())["strata"]
    assert {row["shortfall"] for row in rows} == {2, 3}


def test_fraction_allocation(root):
    out = build_batch(_config(allocation={"fraction": 0.5}))
    assert json.loads((out / "manifest.json").read_text())["total_items"] == 20


def test_ceiling_is_enforced_not_truncated(root):
    with pytest.raises(BatchError, match="max_items"):
        build_batch(_config(max_items=10))


def test_a_built_batch_is_never_rebuilt(root):
    build_batch(_config())
    with pytest.raises(BatchError, match="never rebuilt"):
        build_batch(_config())


def test_any_change_is_detected(root):
    out = build_batch(_config())
    assert verify_batch(out) == []
    (out / "key.jsonl").write_text("tampered\n")
    (out / "notes.txt").write_text("x")
    assert verify_batch(out) == [
        "key.jsonl changed since the batch was frozen",
        "unexpected file notes.txt",
    ]


def test_allocation_needs_exactly_one_rule():
    with pytest.raises(ValueError, match="exactly one"):
        _config(allocation={"per_stratum": 4, "fraction": 0.5})
