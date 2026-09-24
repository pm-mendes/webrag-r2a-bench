"""Benign pages and their adversarial variants.

Adversarial pages are precomputed (one variant per task x family) and stored in the
same WARC archive as the benign pages, so that the archive — and its fingerprint —
fixes exactly what the adversary published.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict

from webrag_bench.attacks import Template, canary, inject
from webrag_bench.core.tasks import Task

_VARIANT_PARAM = "adv"


class _PageEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str
    file: str


class _Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["DEMO", "FROZEN"]
    pages: list[_PageEntry]


@dataclass(frozen=True)
class Page:
    url: str
    html: str


def load_benign_pages(corpus_dir: Path) -> list[Page]:
    manifest = _Manifest.model_validate(
        yaml.safe_load((corpus_dir / "pages.yaml").read_text(encoding="utf-8"))
    )
    return [Page(e.url, (corpus_dir / "pages" / e.file).read_text(encoding="utf-8"))
            for e in manifest.pages]


def adversarial_url(target_url: str, family: str, task_id: str) -> str:
    sep = "&" if "?" in target_url else "?"
    return f"{target_url}{sep}{_VARIANT_PARAM}={family}-{task_id}"


def is_adversarial_url(url: str, family: str | None = None) -> bool:
    marker = f"{_VARIANT_PARAM}="
    if marker not in url:
        return False
    return family is None or url.rsplit(marker, 1)[1].startswith(f"{family}-")


def build_adversarial_pages(benign: list[Page], tasks: list[Task],
                            templates: dict[str, Template], salt: str) -> list[Page]:
    by_url = {p.url: p for p in benign}
    pages = []
    for task in tasks:
        target = by_url.get(task.target_page)
        if target is None:
            raise KeyError(f"task {task.id}: target page {task.target_page} is not in the corpus")
        for family, template in templates.items():
            token = canary(family, task.id, salt)
            html = inject(target.html, template, task.goal_for(token), token)
            pages.append(Page(adversarial_url(task.target_page, family, task.id), html))
    return pages
