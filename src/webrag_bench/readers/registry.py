"""Reader registry. Each reader is recorded with the exact version of its library."""

from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import version

from webrag_bench.readers.bs4_readers import bs4_raw, bs4_text
from webrag_bench.readers.html2text_reader import html2text_markdown
from webrag_bench.readers.trafilatura_reader import trafilatura_main

Reader = Callable[[str], str]

_READERS: dict[str, tuple[Reader, str]] = {
    "bs4-text": (bs4_text, "beautifulsoup4"),
    "bs4-raw": (bs4_raw, "beautifulsoup4"),
    "html2text": (html2text_markdown, "html2text"),
    "trafilatura": (trafilatura_main, "trafilatura"),
}


def get_reader(name: str) -> Reader:
    try:
        return _READERS[name][0]
    except KeyError:
        raise ValueError(f"unknown reader {name!r}; known: {reader_names()}") from None


def reader_version(name: str) -> str:
    package = _READERS[name][1]
    return f"{package}=={version(package)}"


def reader_names() -> list[str]:
    return sorted(_READERS)
