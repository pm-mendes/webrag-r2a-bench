import asyncio
import os
import socket
from pathlib import Path

import pytest

from webrag_bench import RACINE
from webrag_bench.attaques import Gabarit, injecter
from webrag_bench.corpus import HorsCorpus, Page, RejeuWarc, ecrire_warc
from webrag_bench.defenses import DefenseNonSpecifiee, defense
from webrag_bench.enregistrement import valider
from webrag_bench.episode import Contexte, executer
from webrag_bench.gel import GelIncomplet
from webrag_bench.lecteurs import lecteur
from webrag_bench.oracles import Etages
from webrag_bench.plan import Plan
from webrag_bench.reseau import ConnexionInterdite, installer_garde, retirer_garde
from webrag_bench.runner import preparer

PLAN_DEMO = RACINE / "config/plans/repetition-a-blanc.yaml"
KIT = Path(os.environ.get("WEBRAG_KIT_DIR", Path.home() / "overleaf/07-TWEB-R2A/kit"))


def test_schema_identique_au_kit():
    kit = KIT / "schemas/run_record_schema.json"
    if not kit.exists():
        pytest.skip(f"kit introuvable : {kit} (définir WEBRAG_KIT_DIR)")
    assert kit.read_bytes() == (RACINE / "schemas/run_record_schema.json").read_bytes()


def test_garde_reseau_refuse_un_site_tiers():
    installer_garde(set())
    try:
        with pytest.raises(ConnexionInterdite):
            socket.create_connection(("93.184.216.34", 80), timeout=1)
    finally:
        retirer_garde()


def test_rejeu_sans_repli_reseau(tmp_path):
    w = tmp_path / "c.warc"
    ecrire_warc([Page("https://a.test/x", "<html>x</html>")], w)
    r = RejeuWarc(w)
    assert r.get("https://a.test/x") == "<html>x</html>"
    with pytest.raises(HorsCorpus):
        r.get("https://a.test/absente")


def test_warc_reproductible(tmp_path):
    pages = [Page("https://a.test/1", "<p>1</p>"), Page("https://a.test/2", "<p>2</p>")]
    assert ecrire_warc(pages, tmp_path / "a.warc") == ecrire_warc(pages[::-1], tmp_path / "b.warc")


def test_campagne_refusee_tant_que_le_gel_est_incomplet(tmp_path):
    with pytest.raises(GelIncomplet):
        preparer(Plan.charger(RACINE / "config/plans/campagne-P.yaml"), tmp_path)


def test_defense_non_specifiee_n_est_pas_approximee():
    with pytest.raises(DefenseNonSpecifiee):
        defense("progent")


def test_identifiants_deterministes():
    p = Plan.charger(PLAN_DEMO)
    cs = p.cellules()
    assert len(cs) == 10
    ids = [p.id_et_graine(c) for c in cs]
    assert ids == [Plan.charger(PLAN_DEMO).id_et_graine(c) for c in cs]
    assert len({i for i, _ in ids}) == len(ids)


def test_emboitement():
    assert Etages(True, True, True, True).emboitement_respecte()
    assert not Etages(True, False, True, False).emboitement_respecte()


@pytest.mark.parametrize("insertion,survit", [
    ("visible", {"bs4-texte", "bs4-brut", "html2text"}),
    ("commentaire", {"bs4-brut"}),
])
def test_le_lecteur_decide_de_ce_qui_survit(insertion, survit):
    g = Gabarit("F1", "t", "DEMO", insertion, "charge {canari}")
    html = injecter("<html><body><main><p>texte</p></main></body></html>", g,
                    {"outil": "x.y", "arguments": {}}, "CNRTEST")
    for nom in ("bs4-texte", "bs4-brut", "html2text"):
        assert ("CNRTEST" in lecteur(nom)(html)) == (nom in survit), nom


def test_episode_complet_valide_le_schema(tmp_path):
    plan = Plan.charger(PLAN_DEMO)
    warc, h = preparer(plan, tmp_path)
    ctx = Contexte(plan, RejeuWarc(warc), h, "test")
    c = plan.cellules()[0]
    rec = asyncio.run(executer(ctx, c))
    valider(rec)
    assert rec["empreinte_gel"].startswith("NON-GELE:")
    assert "generateur-factice: episode sans valeur de mesure" in rec["erreurs"]
