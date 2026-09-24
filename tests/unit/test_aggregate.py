import importlib.util
import json
import os
from pathlib import Path

import pytest

from webrag_bench.analysis import (
    AggregationError,
    LoadedRun,
    campaign_fragment,
    check_publishable,
    funnel_cell,
    load_run,
    merge_into_master,
    pilot_values,
)

KIT = Path(os.environ.get("WEBRAG_KIT_DIR", Path.home() / "overleaf/07-TWEB-R2A/kit"))


def _record(i, family="F1", defense="none", stages=(1, 1, 0, 0), errors=(), fp="abc", v="freeze-p"):
    e, a, f, x = map(bool, stages)
    return {
        "id_episode": f"ep-{i}",
        "famille_attaque": family,
        "condition_defense": defense,
        "generateur": {"nom": "G1", "id_version": "m"},
        "index_recherche": "bm25",
        "lecteur": {"nom": "bs4-text"},
        "tache": {"id": "T01", "type_action": "action-open"},
        "etages": {"exposition": e, "absorption": a, "effet": f, "action": x},
        "erreurs": list(errors),
        "empreinte_gel": fp,
        "version_banc": v,
        "duree_s": 10.0 + i,
        "horodatage_utc": "2026-09-26T10:00:00Z",
    }


def _run(tmp_path, records):
    run = tmp_path / "run"
    run.mkdir()
    (run / "episodes.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")
    (run / "freeze.json").write_text(json.dumps({"sha256_warc": "w" * 64}))
    return run


def test_end_to_end_rate_is_over_exposed_not_over_all():
    records = [
        _record(0, stages=(1, 1, 1, 1)),
        _record(1, stages=(1, 1, 1, 0)),
        _record(2, stages=(0, 0, 0, 0)),
        _record(3, stages=(0, 0, 0, 0)),
    ]
    cell = funnel_cell(records)
    assert (cell["N"], cell["n_E"], cell["n_X"]) == (4, 2, 1)
    assert cell["taux_action_bout_en_bout"] == 0.5  # n_X / n_E, not n_X / N = 0.25


def test_empty_stage_gives_undefined_conditionals():
    cell = funnel_cell([_record(0, stages=(1, 0, 0, 0))])
    assert cell["p_A_sachant_E"] == 0.0
    assert cell["p_F_sachant_A"] is None
    assert cell["p_X_sachant_F"] is None


def test_nesting_violations_and_unattacked_episodes_are_left_out(tmp_path):
    records = [_record(0), _record(1, errors=["nesting-violated"]), _record(2, family="aucune")]
    run = load_run(_run(tmp_path, records))
    assert run.excluded_nesting == 1
    fragment = campaign_fragment(run, tmp_path / "run", ["family", "defense"])
    assert fragment["entonnoir"]["cellules"]["F1__none"]["N"] == 1


def test_publishable_guards(tmp_path):
    ok = load_run(_run(tmp_path, [_record(0)]))
    check_publishable(ok)
    bad = LoadedRun([], 0, 1, frozenset({"NOT-FROZEN:x", "y"}), frozenset({"abc-dirty"}))
    with pytest.raises(AggregationError) as e:
        check_publishable(bad)
    for reason in ("stub", "not frozen", "different freeze fingerprints", "dirty"):
        assert reason in str(e.value)


def test_merge_keeps_comments_and_other_sections(tmp_path):
    master = tmp_path / "MASTER_VALUES.json"
    master.write_text(
        json.dumps(
            {
                "entonnoir": {"commentaire": "keep me", "cellules": {}},
                "annotation": {"kappa_cohen": "PENDING"},
            }
        )
    )
    written = merge_into_master(
        master, {"entonnoir": {"cellules": {"c": {"N": 1}}}, "_provenance": {"x": 1}}
    )
    out = json.loads(master.read_text())
    assert written == ["entonnoir.cellules"]
    assert out["entonnoir"]["commentaire"] == "keep me"
    assert out["annotation"]["kappa_cohen"] == "PENDING"
    assert "_provenance" not in out


def test_pilot_values(tmp_path):
    run = load_run(_run(tmp_path, [_record(i) for i in range(5)]))
    values = pilot_values(run, window_h=72, workers=24)
    assert values["mediane_s_par_episode"] == 12.0
    assert values["n_episodes_pilote"] == 5
    assert values["verdict_faisabilite"].startswith("fits")


def test_pilot_refuses_stub_episodes(tmp_path):
    run = load_run(_run(tmp_path, [_record(i, errors=["stub-component: x"]) for i in range(3)]))
    with pytest.raises(AggregationError, match="real generators"):
        pilot_values(run, window_h=72, workers=24)


def test_cells_pass_the_kit_funnel_verifier(tmp_path):
    verifier = KIT / "verif/verifier_entonnoir.py"
    if not verifier.exists():
        pytest.skip(f"kit not found at {verifier}")
    spec = importlib.util.spec_from_file_location("verifier_entonnoir", verifier)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    stages = [(1, 1, 1, 1), (1, 1, 1, 0), (1, 1, 0, 0), (1, 0, 0, 0), (0, 0, 0, 0)]
    records = [
        _record(i, family=f, defense=d, stages=stages[i % 5])
        for i, (f, d) in enumerate(
            [(f, d) for f in ("F1", "F2") for d in ("none", "x") for _ in range(7)]
        )
    ]
    fragment = campaign_fragment(
        load_run(_run(tmp_path, records)), tmp_path / "run", ["family", "defense"]
    )
    for name, cell in fragment["entonnoir"]["cellules"].items():
        real_errors = [e for e in module.controler_cellule(name, cell) if not e.startswith("  ")]
        assert real_errors == [], real_errors
