"""Reader built on trafilatura (main-content extraction)."""

from __future__ import annotations

import trafilatura


def trafilatura_main(html: str) -> str:
    return trafilatura.extract(html, include_comments=False) or ""
