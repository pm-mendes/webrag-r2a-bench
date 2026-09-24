"""Attack templates and their insertion into a page.

A template is a YAML file (config/demo/attacks/, config/frozen/attacks/). The exact
text of the four families is a FROZEN element that comes from the manuscript, not
from this repository; demo templates carry `status: DEMO`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict

InsertionPoint = Literal["visible", "css-hidden", "comment", "alt-attribute", "meta"]
INSERTION_POINTS: tuple[str, ...] = ("visible", "css-hidden", "comment", "alt-attribute", "meta")


class _TemplateFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    family: Literal["F1", "F2", "F3", "F4"]
    name: str
    status: Literal["DEMO", "FROZEN"]
    insertion: InsertionPoint
    template: str


@dataclass(frozen=True)
class Template:
    family: str
    name: str
    status: str
    insertion: str
    text: str

    def render(self, goal: dict[str, Any], canary_token: str) -> str:
        return self.text.format(
            canary=canary_token,
            tool=goal["tool"],
            arguments=json.dumps(goal["arguments"], ensure_ascii=False),
        )


def load_templates(directory: Path) -> dict[str, Template]:
    templates: dict[str, Template] = {}
    for path in sorted(directory.glob("*.yaml")):
        f = _TemplateFile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        if f.family in templates:
            raise ValueError(f"{path.name}: family {f.family} is defined twice")
        templates[f.family] = Template(f.family, f.name, f.status, f.insertion, f.template)
    return templates


def inject(html: str, template: Template, goal: dict[str, Any], canary_token: str) -> str:
    """Insert the payload into the page at the template's insertion point.

    The insertion point matters: depending on the reader (HTML -> text), content hidden
    with CSS, a comment or an attribute survives or disappears. This is what makes the
    reader an experimental factor.
    """
    payload = template.render(goal, canary_token)
    escaped = payload.replace('"', "&quot;")
    fragment = {
        "visible": f"<p>{payload}</p>",
        "css-hidden": f'<div style="display:none">{payload}</div>',
        "comment": f"<!-- {payload} -->",
        "alt-attribute": f'<img src="data:," alt="{escaped}">',
        "meta": f'<meta name="description" content="{escaped}">',
    }[template.insertion]
    anchor = "</head>" if template.insertion == "meta" else "</main>"
    if anchor not in html:
        anchor = "</body>"
    if anchor not in html:
        return html + fragment
    return html.replace(anchor, fragment + anchor, 1)
