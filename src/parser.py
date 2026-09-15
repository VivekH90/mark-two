"""Parser for the Mark Two article language."""

import re
from pathlib import Path
from typing import List

from .ast import Button, Document, Environment, Image, RelatedLink, Section, Subsection


_DIRECTIVE = re.compile(r"^\s*@([A-Za-z][\w ]*)\s*\{(.*)\}\s*$")
_ENVIRONMENTS = {"theorem", "lemma", "definition", "corollary"}


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "section"


def _split_top_level(text: str) -> List[str]:
    parts, current = [], []
    quote = None
    depth = 0
    for char in text:
        if char in {'"', "'"}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
        elif quote is None:
            if char in "{[(":
                depth += 1
            elif char in "})]":
                depth = max(0, depth - 1)
            elif char == "," and depth == 0:
                part = "".join(current).strip()
                if part:
                    parts.append(part)
                current = []
                continue
        current.append(char)
    part = "".join(current).strip()
    if part:
        parts.append(part)
    return parts


def _parse_key_values(text: str):
    values = {}
    for part in _split_top_level(text):
        if "=" in part:
            key, value = part.split("=", 1)
            values[key.strip().lower()] = value.strip().strip('"\'')
        elif "name" not in values:
            values["name"] = part.strip().strip('"\'')
    return values


def _unique_slug(base: str, used: set[str]) -> str:
    if base not in used:
        used.add(base)
        return base
    number = 2
    while f"{base}-{number}" in used:
        number += 1
    slug = f"{base}-{number}"
    used.add(slug)
    return slug


def _add_content(container, line: str) -> None:
    if line.strip():
        container.content.append(line.strip())


def parse(source: str) -> Document:
    document = Document()
    current_section = None
    current_subsection = None
    current_environment = None
    used_slugs = set()

    for raw_line in source.splitlines():
        match = _DIRECTIVE.match(raw_line)
        if not match:
            target = current_environment or current_subsection or current_section
            if target is not None:
                _add_content(target, raw_line)
            continue

        command = match.group(1).strip().lower().replace(" ", "")
        argument = match.group(2).strip()

        if command in {"documenttitle", "title", "button", "section", "subsection", "image", "relatedlinks", "relatedlink"}:
            current_environment = None

        if command == "documenttitle":
            values = _parse_key_values(argument)
            document.document_title = values.get("name", argument)
            document.banner = values.get("banner", "")
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
            values = _parse_key_values(argument)
            title = values.get("name", argument)
            current_section = Section(
                title=title,
                color=values.get("color", "#111111"),
                slug=_unique_slug(_slugify(title), used_slugs),
            )
            document.sections.append(current_section)
            current_subsection = None
        elif command == "subsection":
            if current_section is None:
                raise ValueError("@subsection must appear after @section")
            current_subsection = Subsection(
                title=argument,
                slug=_unique_slug(_slugify(argument), used_slugs),
            )
            current_section.subsections.append(current_subsection)
        elif command == "image":
            target = current_subsection or current_section
            if target is None:
                raise ValueError("@image must appear after @section")
            values = _parse_key_values(argument)
            src = values.get("src", "")
            if not src:
                raise ValueError("@image requires src = ...")
            target.content.append(Image(
                src=src,
                alt=values.get("alt", ""),
                caption=values.get("caption", ""),
            ))
        elif command in _ENVIRONMENTS:
            target = current_subsection or current_section
            if target is None:
                raise ValueError(f"@{command} must appear after @section")
            environment = Environment(kind=command, title=argument)
            target.content.append(environment)
            current_environment = environment
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
