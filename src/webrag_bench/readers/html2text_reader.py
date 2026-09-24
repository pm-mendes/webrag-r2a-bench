"""Reader built on html2text (Markdown output)."""

from __future__ import annotations

import html2text


def html2text_markdown(html: str) -> str:
    converter = html2text.HTML2Text()
    converter.ignore_links = True
    converter.ignore_images = False
    converter.body_width = 0
    return str(converter.handle(html))
