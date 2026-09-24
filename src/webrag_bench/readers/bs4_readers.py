"""Readers built on BeautifulSoup."""

from __future__ import annotations

from bs4 import BeautifulSoup, Comment


def _is_comment(s: object) -> bool:
    return isinstance(s, Comment)


def bs4_text(html: str) -> str:
    """All DOM text, including CSS-hidden content; comments dropped."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    for comment in soup.find_all(string=_is_comment):
        comment.extract()
    return soup.get_text(" ", strip=True)


def bs4_raw(html: str) -> str:
    """Naive reader: text, comments, image alt text and meta content."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    parts = [soup.get_text(" ", strip=True)]
    parts += [str(c) for c in soup.find_all(string=_is_comment)]
    parts += [str(img.get("alt", "")) for img in soup.find_all("img")]
    parts += [str(meta.get("content", "")) for meta in soup.find_all("meta")]
    return " ".join(p for p in parts if p)
