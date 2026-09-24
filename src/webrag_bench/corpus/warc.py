"""WARC archive writer and offline replay.

Every page read during an episode goes through `WarcReplay`. A URL missing from the
archive raises `NotInCorpusError`: there is no network fallback.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

from warcio.archiveiterator import ArchiveIterator
from warcio.statusandheaders import StatusAndHeaders
from warcio.warcwriter import WARCWriter

from webrag_bench.corpus.pages import Page

_FIXED_DATE = "2026-01-01T00:00:00Z"


class NotInCorpusError(KeyError):
    pass


def _deterministic_uuid(url: str) -> str:
    h = hashlib.sha256(url.encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def write_warc(pages: list[Page], path: Path) -> str:
    """Write the archive and return its SHA-256.

    Records are sorted by URL and carry a fixed date and deterministic ids, so the
    archive is reproducible byte for byte.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    writer = WARCWriter(buffer, gzip=False)
    for page in sorted(pages, key=lambda p: p.url):
        headers = StatusAndHeaders(
            "200 OK", [("Content-Type", "text/html; charset=utf-8")], protocol="HTTP/1.1"
        )
        record = writer.create_warc_record(
            page.url,
            "response",
            payload=io.BytesIO(page.html.encode("utf-8")),
            http_headers=headers,
            warc_headers_dict={
                "WARC-Date": _FIXED_DATE,
                "WARC-Record-ID": f"<urn:uuid:{_deterministic_uuid(page.url)}>",
            },
        )
        writer.write_record(record)
    data = buffer.getvalue()
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


class WarcReplay:
    """Serves archived responses, and nothing else."""

    def __init__(self, path: Path) -> None:
        self._pages: dict[str, str] = {}
        with path.open("rb") as f:
            for record in ArchiveIterator(f):
                if record.rec_type == "response":
                    url = record.rec_headers.get_header("WARC-Target-URI")
                    self._pages[url] = record.content_stream().read().decode("utf-8")

    def get(self, url: str) -> str:
        try:
            return self._pages[url]
        except KeyError:
            raise NotInCorpusError(
                f"{url} is not in the WARC archive (no network access)"
            ) from None

    def urls(self) -> list[str]:
        return sorted(self._pages)
