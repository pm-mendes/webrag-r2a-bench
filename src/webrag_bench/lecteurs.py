"""Lecteurs : convertisseurs HTML -> texte, traités comme facteur expérimental.

Le lecteur décide de ce que l'adversaire contrôle : un `display:none`, un commentaire
ou un attribut `alt` survit à certains convertisseurs et pas à d'autres. Chaque
lecteur est enregistré avec la version exacte de sa bibliothèque.
"""

from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import version

from bs4 import BeautifulSoup, Comment


def _bs4_texte(html: str) -> str:
    """Tout le texte du DOM, y compris le contenu caché en CSS ; sans commentaires."""
    soupe = BeautifulSoup(html, "html.parser")
    for t in soupe(["script", "style"]):
        t.decompose()
    for c in soupe.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    return soupe.get_text(" ", strip=True)


def _bs4_brut(html: str) -> str:
    """Lecteur naïf : texte, commentaires, attributs alt et meta description."""
    soupe = BeautifulSoup(html, "html.parser")
    for t in soupe(["script", "style"]):
        t.decompose()
    morceaux = [soupe.get_text(" ", strip=True)]
    morceaux += [str(c) for c in soupe.find_all(string=lambda s: isinstance(s, Comment))]
    morceaux += [i.get("alt", "") for i in soupe.find_all("img")]
    morceaux += [m.get("content", "") for m in soupe.find_all("meta")]
    return " ".join(m for m in morceaux if m)


def _html2text(html: str) -> str:
    import html2text

    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = False
    h.body_width = 0
    return h.handle(html)


def _trafilatura(html: str) -> str:
    import trafilatura

    return trafilatura.extract(html, include_comments=False) or ""


_LECTEURS: dict[str, tuple[Callable[[str], str], str]] = {
    "bs4-texte": (_bs4_texte, "beautifulsoup4"),
    "bs4-brut": (_bs4_brut, "beautifulsoup4"),
    "html2text": (_html2text, "html2text"),
    "trafilatura": (_trafilatura, "trafilatura"),
}


def lecteur(nom: str) -> Callable[[str], str]:
    return _LECTEURS[nom][0]


def version_lecteur(nom: str) -> str:
    return f"{_LECTEURS[nom][1]}=={version(_LECTEURS[nom][1])}"


def noms_lecteurs() -> list[str]:
    return sorted(_LECTEURS)
