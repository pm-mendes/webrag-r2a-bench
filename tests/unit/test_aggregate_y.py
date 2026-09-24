import json
import os
import shutil
from pathlib import Path

import pytest

from webrag_bench.analysis import AggregationError, merge_into_master
from webrag_bench.analysis.aggregate_y import y_fragment

KIT_Y = Path(os.environ.get("WEBRAG_KIT_Y_DIR", Path.home() / "overleaf/08-TWEB-PBD/kit"))


def _cell(family, provenance, defense, fault, task="T01"):
    return {
        "subplan": "m",
        "task": task,
        "family": family,
        "defense": defense,
        "generator": "g",
        "index": "bm25",
        "reader": "r",
        "repetition": 0,
        "provenance": provenance,
        "fault_rate": fault,
    }


def _run(tmp_path):
    specs = [  # (id, family, provenance, defense, fault, utility, effects, crypto ms, duration)
        ("e1", "none", "off", "none", 0.0, True, "A", 0.0, 1.0),
        ("e2", "none", "on", "none", 0.0, True, "A", 2.0, 1.1),
        ("e3", "none", "on", "pol", 0.0, True, "A", 2.0, 1.1),
        ("e4", "F1", "on", "pol", 0.0, True, "A", 4.0, 1.2),
        ("e5", "none", "on", "pol", 0.5, False, "B", 2.0, 1.0),
    ]
    run = tmp_path / "run"
    run.mkdir()
    with (run / "measures.jsonl").open("w") as m, (run / "episodes.jsonl").open("w") as e:
        for eid, fam, prov, dfn, fault, util, eff, ms, dur in specs:
            m.write(
                json.dumps(
                    {
                        "id_episode": eid,
                        "cell": _cell(fam, prov, dfn, fault),
                        "utility": util,
                        "effects_digest": eff,
                        "provenance": {
                            "cost": {"sign_ms": ms / 2, "verify_ms": ms / 2, "meta_bytes": 100}
                        },
                    }
                )
                + "\n"
            )
            e.write(json.dumps({"id_episode": eid, "duree_s": dur}) + "\n")
    return run


def test_y_fragment(tmp_path):
    f = y_fragment(_run(tmp_path), policy="pol", partial_rate=0.5)
    assert f["cout_delegation"]["surcout_latence_ms_median"] == 2.0  # e2, e3, e4: 2, 2, 4
    assert f["cout_delegation"]["surcout_taille_message_octets"] == 100
    assert f["degradation_gracieuse"] == {
        "utilite_sans_provenance": 1.0,
        "utilite_avec_provenance": 1.0,
        "utilite_sous_defaillance_partielle": 0.0,
    }
    assert f["egalite_inter_episodes"] == {
        "n_paires_testees": 1,
        "taux_egalite_observe": 1.0,
        "violations": 0,
    }
    assert f["_provenance"]["delegation_cost_end_to_end"]["end_to_end_pairs"] == 1
    assert "borne_formelle_predite" not in f["cout_delegation"]


def test_missing_policy_is_an_error(tmp_path):
    with pytest.raises(AggregationError, match="no clean/attacked pair"):
        y_fragment(_run(tmp_path), policy="pbd", partial_rate=0.5)


def test_merge_refuses_undeclared_keys(tmp_path):
    master = tmp_path / "M.json"
    master.write_text(json.dumps({"cout_delegation": {"surcout_latence_ms_median": "PENDING"}}))
    with pytest.raises(AggregationError, match=r"cout_delegation\.typo"):
        merge_into_master(master, {"cout_delegation": {"typo": 1}})
    assert (
        json.loads(master.read_text())["cout_delegation"]["surcout_latence_ms_median"] == "PENDING"
    )


def test_fragment_fits_the_real_y_master(tmp_path):
    source = KIT_Y / "MASTER_VALUES.json"
    if not source.exists():
        pytest.skip(f"kit not found at {source}")
    copy = tmp_path / "MASTER_VALUES.json"
    shutil.copy(source, copy)
    written = merge_into_master(copy, y_fragment(_run(tmp_path), "pol", 0.5))
    assert len(written) == 9
    assert json.loads(copy.read_text())["cout_delegation"]["borne_formelle_predite"] == "PENDING"
