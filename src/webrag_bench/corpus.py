"""Corpus de pages et archive WARC, avec proxy de rejeu hors ligne.

Le corpus est construit une fois, écrit dans une archive WARC, et toute lecture de
page pendant un épisode passe par `RejeuWarc`. Une URL absente de l'archive lève
`HorsCorpus` : il n'y a pas de repli réseau.

Les pages adverses sont précalculées dans la même archive (une variante par
couple tâche × famille), pour que l'archive — et son empreinte — fixe exactement
ce que l'adversaire a publié.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from pathlib import Path

import yaml
from warcio.archiveiterator import ArchiveIterator
from warcio.statusandheaders import StatusAndHeaders
from warcio.warcwriter import WARCWriter

from webrag_bench.attaques import Gabarit, canari, injecter
from webrag_bench.taches import Tache


class HorsCorpus(KeyError):
    pass


@dataclass(frozen=True)
class Page:
    url: str
    html: str
    adverse: bool = False
    famille: str | None = None
    tache: str | None = None


def charger_pages_benignes(dossier_corpus: Path) -> list[Page]:
    manifeste = yaml.safe_load((dossier_corpus / "pages.yaml").read_text(encoding="utf-8"))
    pages = []
    for entree in manifeste["pages"]:
        html = (dossier_corpus / "pages" / entree["fichier"]).read_text(encoding="utf-8")
        pages.append(Page(url=entree["url"], html=html))
    return pages


def url_adverse(url_cible: str, famille: str, tache_id: str) -> str:
    sep = "&" if "?" in url_cible else "?"
    return f"{url_cible}{sep}v={famille}-{tache_id}"


def construire_pages_adverses(
    benignes: list[Page], taches: list[Tache], gabarits: dict[str, Gabarit], sel: str
) -> list[Page]:
    par_url = {p.url: p for p in benignes}
    adverses = []
    for t in taches:
        cible = par_url.get(t.page_cible)
        if cible is None:
            raise HorsCorpus(f"tâche {t.id} : page_cible {t.page_cible} absente du corpus")
        for fam, g in gabarits.items():
            c = canari(fam, t.id, sel)
            html = injecter(cible.html, g, t.but_adverse_rendu(c), c)
            adverses.append(
                Page(url=url_adverse(t.page_cible, fam, t.id), html=html,
                     adverse=True, famille=fam, tache=t.id)
            )
    return adverses


def ecrire_warc(pages: list[Page], chemin: Path) -> str:
    """Écrit l'archive et renvoie son empreinte SHA-256 (ordre des URL déterministe)."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    tampon = io.BytesIO()
    ecrivain = WARCWriter(tampon, gzip=False)
    for p in sorted(pages, key=lambda p: p.url):
        corps = p.html.encode("utf-8")
        entetes = StatusAndHeaders(
            "200 OK", [("Content-Type", "text/html; charset=utf-8")], protocol="HTTP/1.1"
        )
        # WARC-Date fixe : l'archive doit être reproductible octet pour octet
        rec = ecrivain.create_warc_record(
            p.url, "response", payload=io.BytesIO(corps), http_headers=entetes,
            warc_headers_dict={"WARC-Date": "2026-01-01T00:00:00Z",
                               "WARC-Record-ID": "<urn:uuid:"
                               + _uuid_det(p.url) + ">"},
        )
        ecrivain.write_record(rec)
    donnees = tampon.getvalue()
    chemin.write_bytes(donnees)
    return hashlib.sha256(donnees).hexdigest()


def _uuid_det(url: str) -> str:
    h = hashlib.sha256(url.encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


class RejeuWarc:
    """Proxy de rejeu : sert les réponses archivées, rien d'autre."""

    def __init__(self, chemin: Path) -> None:
        self._pages: dict[str, str] = {}
        with chemin.open("rb") as f:
            for rec in ArchiveIterator(f):
                if rec.rec_type != "response":
                    continue
                url = rec.rec_headers.get_header("WARC-Target-URI")
                self._pages[url] = rec.content_stream().read().decode("utf-8")

    def get(self, url: str) -> str:
        try:
            return self._pages[url]
        except KeyError:
            raise HorsCorpus(f"{url} absente de l'archive WARC — aucun accès réseau") from None

    def urls(self) -> list[str]:
        return sorted(self._pages)
