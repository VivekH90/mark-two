"""Parser for the first Mark Two article syntax.

Supported directives:
    @documenttitle{...}
    @button{name, href = ..., color = ...}
    @title{...}
    @section{...}
    @subsection{...}
    @relatedlinks{...}

Plain text between structural directives becomes article content.  The parser
is deliberately small so the language can evolve without fighting a large
parsing framework.
"""

import re
from pathlib import Path
from typing import List

from .ast import Button, Document, RelatedLink, Section, Subsection


_DIRECTIVE = re.compile(r"^\s*@([A-Za-z][\w ]*)\s*\{(.*)\}\s*$")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "section"


def _split_top_level(text: str) -> List[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


def _parse_key_values(text: str):
    values = {}
    for part in _split_top_level(text):
        if "=" in part:
            key, value = part.split("=", 1)
            values[key.strip().lower()] = value.strip().strip('"\'')
        elif "name" not in values:
            values["name"] = part.strip().strip('"\'')
    return values


def _add_content(container, line: str) -> None:
    if line.strip():
        container.content.append(line.strip())


def parse(source: str) -> Document:
    document = Document()
    current_section = None
    current_subsection = None

    for raw_line in source.splitlines():
        match = _DIRECTIVE.match(raw_line)
        if not match:
            target = current_subsection or current_section
            if target is not None:
                _add_content(target, raw_line)
            continue

        command = match.group(1).strip().lower().replace(" ", "")
        argument = match.group(2).strip()

        if command == "documenttitle":
            document.document_title = argument
        elif command == "title":
            document.article_title = argument
        elif command == "button":
            values = _parse_key_values(argument)
            document.buttons.append(Button(
                name=values.get("name", "Button"),
                href=values.get("href", "#"),
                color=values.get("color", "black"),
            ))
        elif command == "section":
            current_section = Section(title=argument, slug=_slugify(argument))
            document.sections.append(current_section)
            current_subsection = None
        elif command == "subsection":
            if current_section is None:
                raise ValueError("@subsection must appear after @section")
            current_subsection = Subsection(title=argument, slug=_slugify(argument))
            current_section.subsections.append(current_subsection)
        elif command in {"relatedlinks", "relatedlink"}:
            values = _parse_key_values(argument)
            if "href" not in values:
                raise ValueError("@relatedlinks requires href = ...")
            document.related_links.append(RelatedLink(
                name=values.get("name", "Related link"),
                href=values["href"],
            ))
        else:
            raise ValueError(f"Unknown Mark Two directive: @{match.group(1)}")

    return document


def parse_file(path: str | Path) -> Document:
    return parse(Path(path).read_text(encoding="utf-8"))
