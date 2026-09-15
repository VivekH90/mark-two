"""Parser for the Mark Two article language."""

import re
from pathlib import Path
from typing import List

from .ast import Button, Document, Environment, Image, Label, ListBlock, ListItem, MathBlock, Reference, RelatedLink, Section, Subsection


_DIRECTIVE = re.compile(r"^\s*@([A-Za-z][\w ]*)\s*\{(.*)\}\s*$")
_ENVIRONMENTS = {
    "theorem", "lemma", "definition", "corollary", "axiom",
    "proposition", "remark", "example", "conjecture", "notation", "warning", "proof",
}
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
            if quote == char: quote = None
            elif quote is None: quote = char
        elif quote is None:
            if char in "{[(": depth += 1
            elif char in "})]": depth = max(0, depth - 1)
            elif char == "," and depth == 0:
                part = "".join(current).strip()
                if part: parts.append(part)
                current = []
                continue
        current.append(char)
    part = "".join(current).strip()
    if part: parts.append(part)
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
        used.add(base); return base
    number = 2
    while f"{base}-{number}" in used: number += 1
    slug = f"{base}-{number}"; used.add(slug); return slug


def _extract_directive_blocks(text: str, command: str):
    prefix = re.compile(rf"@{re.escape(command)}\s*\{{", re.IGNORECASE)
    blocks, position = [], 0
    while True:
        match = prefix.search(text, position)
        if not match: break
        start, brace_start = match.start(), match.end() - 1
        depth, quote, end = 0, None, None
        for index in range(brace_start, len(text)):
            char = text[index]
            if char in {'"', "'"}:
                if quote == char: quote = None
                elif quote is None: quote = char
            elif quote is None:
                if char == "{": depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0: end = index; break
        if end is None: raise ValueError(f"Unclosed @{command}{{...}} block")
        blocks.append((start, end + 1, text[brace_start + 1:end])); position = end + 1
    return blocks


def _parse_list_item_content(body: str):
    return parse(f"@section{{List item}}\n{body}").sections[0].content


def _parse_list(argument: str, ordered: bool) -> ListBlock:
    color = "black"
    parts = _split_top_level(argument); item_parts = []
    for part in parts:
        if "=" in part and not part.lstrip().lower().startswith("@item"):
            key, value = part.split("=", 1)
            if key.strip().lower() == "color":
                color = value.strip().strip('"\'') or "black"; continue
        item_parts.append(part)
    item_text = ",".join(item_parts); blocks = _extract_directive_blocks(item_text, "item")
    items, position = [], 0
    for start, end, body in blocks:
        if item_text[position:start].strip().strip(",").strip(): raise ValueError("Only @item{...} entries may appear inside @enumerate or @itemize")
        title = ""
        title_match = re.match(r"\s*title\s*=\s*(?:\"((?:[^\"\\]|\\.)*)\"|'((?:[^'\\]|\\.)*)')\s*,?\s*(.*)\Z", body, re.DOTALL | re.IGNORECASE)
        if title_match:
            title = (title_match.group(1) if title_match.group(1) is not None else title_match.group(2)).strip(); body = title_match.group(3).strip()
        items.append(ListItem(content=_parse_list_item_content(body), title=title)); position = end
    if item_text[position:].strip().strip(",").strip(): raise ValueError("Only @item{...} entries may appear inside @enumerate or @itemize")
    if not items: raise ValueError("@enumerate or @itemize requires at least one @item{...}")
    return ListBlock(ordered=ordered, items=items, color=color)


def _add_content(container, line: str) -> None:
    if line.strip(): container.content.append(line.strip())


def _title_and_label(argument: str):
    values = _parse_key_values(argument)
    return values.get("name", ""), values.get("label", "")


def parse(source: str) -> Document:
    document = Document(); current_section = None; current_subsection = None; current_environment = None
    used_slugs = set(); display_math_lines = None; lines = source.splitlines(); index = 0
    while index < len(lines):
        raw_line = lines[index]
        if display_math_lines is not None:
            if raw_line.strip() == r"\]":
                target = current_environment or current_subsection or current_section
                if target is None: raise ValueError("display math must appear after @section")
                target.content.append(MathBlock("\n".join(display_math_lines))); display_math_lines = None
            else: display_math_lines.append(raw_line)
            index += 1; continue
        if raw_line.strip() == r"\[": display_math_lines = []; index += 1; continue

        match = _DIRECTIVE.match(raw_line)
        if not match:
            target = current_environment or current_subsection or current_section
            if target is not None: _add_content(target, raw_line)
            index += 1; continue

        command = match.group(1).strip().lower().replace(" ", ""); argument = match.group(2).strip()
        if command in {"documenttitle", "title", "button", "section", "subsection", "image", "relatedlinks", "relatedlink", "enumerate", "itemize"}:
            current_environment = None

        if command == "documenttitle":
            values = _parse_key_values(argument)
            document.document_title = values.get("name", argument)
            document.banner = values.get("banner", "")
            document.banner_color = values.get("color", "")
        elif command == "title": document.article_title = argument
        elif command == "button":
            values = _parse_key_values(argument); document.buttons.append(Button(name=values.get("name", "Button"), href=values.get("href", "#"), color=values.get("color", "black")))
        elif command == "section":
            values = _parse_key_values(argument); title = values.get("name", argument)
            current_section = Section(title=title, color=values.get("color", "#111111"), slug=_unique_slug(_slugify(title), used_slugs), label=values.get("label", "")); document.sections.append(current_section); current_subsection = None
        elif command == "subsection":
            if current_section is None: raise ValueError("@subsection must appear after @section")
            title, label = _title_and_label(argument); title = title or argument
            current_subsection = Subsection(title=title, slug=_unique_slug(_slugify(title), used_slugs), label=label); current_section.subsections.append(current_subsection)
        elif command == "image":
            target = current_environment or current_subsection or current_section
            if target is None: raise ValueError("@image must appear after @section")
            values = _parse_key_values(argument); src = values.get("src", "")
            if not src: raise ValueError("@image requires src = ...")
            target.content.append(Image(src=src, alt=values.get("alt", ""), caption=values.get("caption", ""), label=values.get("label", "")))
        elif command == "label":
            target = current_environment or current_subsection or current_section
            if target is None: raise ValueError("@label must appear after @section")
            label = argument.strip().strip('"\'')
            if not label: raise ValueError("@label requires a label name")
            target.content.append(Label(name=label))
        elif command == "ref":
            target = current_environment or current_subsection or current_section
            if target is None: raise ValueError("@ref must appear after @section")
            values = _parse_key_values(argument); target_name = values.get("name", argument)
            target.content.append(Reference(target=target_name, text=values.get("text", "")))
        elif command in _ENVIRONMENTS:
            target = current_subsection or current_section
            if target is None: raise ValueError(f"@{command} must appear after @section")
            title, label = _title_and_label(argument)
            environment = Environment(kind=command, title=title or (argument if command != "proof" else ""), label=label)
            target.content.append(environment); current_environment = environment
        elif command in _LIST_ENVIRONMENTS:
            target = current_environment or current_subsection or current_section
            if target is None: raise ValueError(f"@{command} must appear after @section")
            target.content.append(_parse_list(argument, ordered=(command == "enumerate")))
        elif command in {"relatedlinks", "relatedlink"}:
            values = _parse_key_values(argument)
            if "href" not in values: raise ValueError("@relatedlinks requires href = ...")
            document.related_links.append(RelatedLink(name=values.get("name", "Related link"), href=values["href"]))
        else: raise ValueError(f"Unknown Mark Two directive: @{match.group(1)}")
        index += 1
    if display_math_lines is not None: raise ValueError("Unclosed display math block: expected \\]")
    return document


def parse_file(path: str | Path) -> Document:
    return parse(Path(path).read_text(encoding="utf-8"))
