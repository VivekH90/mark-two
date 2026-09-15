"""Parser for the Mark Two article language."""

import re
from pathlib import Path
from typing import List

from .ast import Button, Document, Environment, Image, ListBlock, MathBlock, RelatedLink, Section, Subsection


_DIRECTIVE = re.compile(r"^\s*@([A-Za-z][\w ]*)\s*\{(.*)\}\s*$")
_ENVIRONMENTS = {"theorem", "lemma", "definition", "corollary"}
_LIST_ENVIRONMENTS = {"enumerate", "itemize"}


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


def _parse_list(argument: str, ordered: bool) -> ListBlock:
    """Parse @enumerate{...} or @itemize{...}. Items are @item{...}."""
    color = "black"
    item_text = argument

    # Allow @enumerate{color = green, @item{...}, @item{...}}.
    parts = _split_top_level(argument)
    if parts and "=" in parts[0] and not parts[0].lstrip().startswith("@item"):
        key, value = parts[0].split("=", 1)
        if key.strip().lower() == "color":
            color = value.strip().strip('"\'') or "black"
            item_text = ",".join(parts[1:])

    items = []
    pattern = re.compile(r"@item\s*\{([^{}]*)\}", re.DOTALL)
    position = 0
    for match in pattern.finditer(item_text):
        if item_text[position:match.start()].strip().strip(",").strip():
            raise ValueError("Only @item{...} entries may appear inside @enumerate or @itemize")
        items.append(match.group(1).strip())
        position = match.end()
    if item_text[position:].strip().strip(",").strip():
        raise ValueError("Only @item{...} entries may appear inside @enumerate or @itemize")
    if not items:
        raise ValueError("@enumerate or @itemize requires at least one @item{...}")
    return ListBlock(ordered=ordered, items=items, color=color)


def _add_content(container, line: str) -> None:
    if line.strip():
        container.content.append(line.strip())


def parse(source: str) -> Document:
    document = Document()
    current_section = None
    current_subsection = None
    current_environment = None
    used_slugs = set()
    display_math_lines = None

    lines = source.splitlines()
    index = 0
    while index < len(lines):
        raw_line = lines[index]

        if display_math_lines is not None:
            if raw_line.strip() == r"\]":
                target = current_environment or current_subsection or current_section
                if target is None:
                    raise ValueError("display math must appear after @section")
                target.content.append(MathBlock("\n".join(display_math_lines)))
                display_math_lines = None
            else:
                display_math_lines.append(raw_line)
            index += 1
            continue

        if raw_line.strip() == r"\[":
            display_math_lines = []
            index += 1
            continue

        match = _DIRECTIVE.match(raw_line)
        if not match:
            target = current_environment or current_subsection or current_section
            if target is not None:
                _add_content(target, raw_line)
            index += 1
            continue

        command = match.group(1).strip().lower().replace(" ", "")
        argument = match.group(2).strip()

        if command in {"documenttitle", "title", "button", "section", "subsection", "image", "relatedlinks", "relatedlink", "enumerate", "itemize"}:
            current_environment = None

        if command == "documenttitle":
            values = _parse_key_values(argument)
            document.document_title = values.get("name", argument)
            document.banner = values.get("banner", "")
        elif command == "title":
            document.article_title = argument
        elif command == "button":
            values = _parse_key_values(argument)
            document.buttons.append(Button(name=values.get("name", "Button"), href=values.get("href", "#"), color=values.get("color", "black")))
        elif command == "section":
            values = _parse_key_values(argument)
            title = values.get("name", argument)
            current_section = Section(title=title, color=values.get("color", "#111111"), slug=_unique_slug(_slugify(title), used_slugs))
            document.sections.append(current_section)
            current_subsection = None
        elif command == "subsection":
            if current_section is None:
                raise ValueError("@subsection must appear after @section")
            current_subsection = Subsection(title=argument, slug=_unique_slug(_slugify(argument), used_slugs))
            current_section.subsections.append(current_subsection)
        elif command == "image":
            target = current_subsection or current_section
            if target is None:
                raise ValueError("@image must appear after @section")
            values = _parse_key_values(argument)
            src = values.get("src", "")
            if not src:
                raise ValueError("@image requires src = ...")
            target.content.append(Image(src=src, alt=values.get("alt", ""), caption=values.get("caption", "")))
        elif command in _ENVIRONMENTS:
            target = current_subsection or current_section
            if target is None:
                raise ValueError(f"@{command} must appear after @section")
            environment = Environment(kind=command, title=argument)
            target.content.append(environment)
            current_environment = environment
        elif command in _LIST_ENVIRONMENTS:
            target = current_environment or current_subsection or current_section
            if target is None:
                raise ValueError(f"@{command} must appear after @section")
            target.content.append(_parse_list(argument, ordered=(command == "enumerate")))
        elif command in {"relatedlinks", "relatedlink"}:
            values = _parse_key_values(argument)
            if "href" not in values:
                raise ValueError("@relatedlinks requires href = ...")
            document.related_links.append(RelatedLink(name=values.get("name", "Related link"), href=values["href"]))
        else:
            raise ValueError(f"Unknown Mark Two directive: @{match.group(1)}")

        index += 1

    if display_math_lines is not None:
        raise ValueError("Unclosed display math block: expected \\]")

    return document


def parse_file(path: str | Path) -> Document:
    return parse(Path(path).read_text(encoding="utf-8"))
