"""Parser for the Mark Two article language."""

import re
from pathlib import Path
from typing import List

from .ast import (
    Button, Document, Environment, Image, Label, ListBlock, ListItem,
    MathBlock, Reference, RelatedLink, Section, Subsection, TextBlock,
)

_DIRECTIVE_START = re.compile(r"^\s*@([A-Za-z][\w ]*)\s*\{")
_ENVIRONMENTS = {
    "theorem", "lemma", "definition", "corollary", "axiom", "proposition",
    "remark", "example", "conjecture", "notation", "warning", "proof",
}
_LIST_ENVIRONMENTS = {"enumerate", "itemize"}


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "section"


def _split_top_level(text: str) -> List[str]:
    parts, current = [], []
    quote = None
    depth = 0
    escaped = False
    for char in text:
        if escaped:
            escaped = False
            current.append(char)
            continue
        if char == "\\":
            escaped = True
            current.append(char)
            continue
        if char == '"':
            quote = None if quote == char else char if quote is None else quote
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


def _strip_quotes(value: str) -> str:
    return value.strip().strip('"\'')


def _parse_key_values(text: str):
    values = {}
    for part in _split_top_level(text):
        if "=" in part:
            key, value = part.split("=", 1)
            values[key.strip().lower()] = _strip_quotes(value)
        elif "name" not in values:
            values["name"] = _strip_quotes(part)
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


def _extract_directive(lines: List[str], start_index: int):
    """Extract one balanced directive starting at a source line."""
    match = _DIRECTIVE_START.match(lines[start_index])
    if not match:
        return None

    command = match.group(1)
    brace_start = match.end() - 1
    depth = 0
    quote = None
    escaped = False
    argument_parts = []

    for line_index in range(start_index, len(lines)):
        line = lines[line_index]
        offset = brace_start if line_index == start_index else 0
        current = []
        for position, char in enumerate(line[offset:], start=offset):
            if escaped:
                escaped = False
                current.append(char)
                continue
            if char == "\\":
                escaped = True
                current.append(char)
                continue
            if char == '"':
                quote = None if quote == char else char if quote is None else quote
                current.append(char)
                continue
            if quote is None and char == "{":
                depth += 1
                if depth > 1:
                    current.append(char)
                continue
            if quote is None and char == "}":
                depth -= 1
                if depth == 0:
                    if line[position + 1:].strip():
                        raise ValueError(f"Unexpected text after @{command}{{...}} directive")
                    argument_parts.append("".join(current).rstrip())
                    return command, "\n".join(argument_parts).strip(), line_index
                current.append(char)
                continue
            current.append(char)
        argument_parts.append("".join(current))

    raise ValueError(f"Unclosed @{command}{{...}} block")


def _extract_directive_blocks(text: str, command: str):
    prefix = re.compile(rf"@{re.escape(command)}\s*\{{", re.IGNORECASE)
    blocks, position = [], 0
    while True:
        match = prefix.search(text, position)
        if not match:
            break
        start = match.start()
        brace_start = match.end() - 1
        depth, quote, end, escaped = 0, None, None, False
        for index in range(brace_start, len(text)):
            char = text[index]
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                quote = None if quote == char else char if quote is None else quote
                continue
            if quote is None and char == "{":
                depth += 1
            elif quote is None and char == "}":
                depth -= 1
                if depth == 0:
                    end = index
                    break
        if end is None:
            raise ValueError(f"Unclosed @{command}{{...}} block")
        blocks.append((start, end + 1, text[brace_start + 1:end]))
        position = end + 1
    return blocks


def _parse_image_group(argument: str, group_id: int):
    values = _parse_key_values(argument)
    indexed_sources, indexed_widths, indexed_heights = {}, {}, {}
    for key, value in values.items():
        source = re.fullmatch(r"image\((\d+)\)", key, re.IGNORECASE)
        width = re.fullmatch(r"width\((\d+)\)", key, re.IGNORECASE)
        height = re.fullmatch(r"height\((\d+)\)", key, re.IGNORECASE)
        if source:
            indexed_sources[int(source.group(1))] = value
        elif width:
            indexed_widths[int(width.group(1))] = value
        elif height:
            indexed_heights[int(height.group(1))] = value

    if not indexed_sources:
        src = values.get("src", values.get("image", ""))
        if not src:
            raise ValueError("@image requires src = ... or image = ...")
        return [Image(
            src=src, alt=values.get("alt", ""), caption=values.get("caption", ""),
            label=values.get("label", ""), width=values.get("width", ""),
            height=values.get("height", ""), group=group_id,
        )]

    indexes = sorted(indexed_sources)
    if indexes != list(range(1, len(indexes) + 1)) or len(indexes) < 2:
        raise ValueError("Multi-image @image blocks must use image(1), image(2), ... entries")

    legacy_width = values.get("width", "")
    legacy_height = values.get("height", "")
    return [Image(
        src=indexed_sources[index],
        alt=values.get(f"alt({index})", values.get("alt", "")),
        caption=values.get("caption", ""),
        label=values.get("label", ""),
        width=indexed_widths.get(index, legacy_width if index == 1 else ""),
        height=indexed_heights.get(index, legacy_height),
        group=group_id,
    ) for index in indexes]


def _parse_list_item_content(body: str):
    return parse(f"@section{{List item}}\n{body}").sections[0].content


def _parse_list(argument: str, ordered: bool) -> ListBlock:
    color = "black"
    item_parts = []
    for part in _split_top_level(argument):
        if "=" in part and not part.lstrip().lower().startswith("@item"):
            key, value = part.split("=", 1)
            if key.strip().lower() == "color":
                color = _strip_quotes(value) or "black"
                continue
        item_parts.append(part)

    item_text = ",".join(item_parts)
    blocks = _extract_directive_blocks(item_text, "item")
    items, position = [], 0
    for start, end, body in blocks:
        if item_text[position:start].strip().strip(",").strip():
            raise ValueError("Only @item{...} entries may appear inside @enumerate or @itemize")
        title = ""
        title_match = re.match(
            r"\s*title\s*=\s*(?:\"((?:[^\"\\]|\\.)*)\"|'((?:[^'\\]|\\.)*)')\s*,?\s*(.*)\Z",
            body, re.DOTALL | re.IGNORECASE,
        )
        if title_match:
            title = (title_match.group(1) or title_match.group(2)).strip()
            body = title_match.group(3).strip()
        items.append(ListItem(content=_parse_list_item_content(body), title=title))
        position = end

    if item_text[position:].strip().strip(",").strip():
        raise ValueError("Only @item{...} entries may appear inside @enumerate or @itemize")
    if not items:
        raise ValueError("@enumerate or @itemize requires at least one @item{...}")
    return ListBlock(ordered=ordered, items=items, color=color)


def _parse_text(argument: str) -> TextBlock:
    if "=" not in argument:
        return TextBlock(text=argument.strip())
    values = _parse_key_values(argument)
    text = values.get("text", values.get("name", ""))
    if not text:
        raise ValueError("@text requires text = ... or plain text content")
    bold = values.get("bold", "false").strip().lower() in {"true", "yes", "1", "on"}
    italic = values.get("italic", "false").strip().lower() in {"true", "yes", "1", "on"}
    return TextBlock(text=text, bold=bold, italic=italic, color=values.get("color", ""))


def _add_content(container, line: str) -> None:
    if line.strip():
        container.content.append(line.strip())


def _title_and_label(argument: str):
    values = _parse_key_values(argument)
    return values.get("name", ""), values.get("label", "")


def parse(source: str) -> Document:
    document = Document()
    current_section = None
    current_subsection = None
    current_environment = None
    current_text = None
    used_slugs = set()
    display_math_lines = None
    lines = source.splitlines()
    index = 0
    image_group_id = 0

    while index < len(lines):
        raw_line = lines[index]
        if display_math_lines is not None:
            if raw_line.strip() == r"\]":
                target = current_text or current_environment or current_subsection or current_section
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

        directive = _extract_directive(lines, index)
        if directive is None:
            target = current_text or current_environment or current_subsection or current_section
            if target is not None:
                _add_content(target, raw_line)
            index += 1
            continue

        command, argument, end_index = directive
        command = command.strip().lower().replace(" ", "")
        if command in {"documenttitle", "author", "title", "button", "section", "subsection", "image", "relatedlinks", "relatedlink", "text"}:
            current_environment = None
            current_text = None

        if command == "documenttitle":
            values = _parse_key_values(argument)
            document.document_title = values.get("name", argument)
            document.banner = values.get("banner", "")
            document.banner_color = values.get("color", "")
        elif command == "author":
            values = _parse_key_values(argument)
            document.author = values.get("name", argument)
        elif command == "title":
            document.article_title = argument
        elif command == "button":
            values = _parse_key_values(argument)
            document.buttons.append(Button(name=values.get("name", "Button"), href=values.get("href", "#"), color=values.get("color", "black")))
        elif command == "section":
            values = _parse_key_values(argument)
            title = values.get("name", argument)
            current_section = Section(title=title, color=values.get("color", "#111111"), slug=_unique_slug(_slugify(title), used_slugs), label=values.get("label", ""))
            document.sections.append(current_section)
            current_subsection = None
        elif command == "subsection":
            if current_section is None:
                raise ValueError("@subsection must appear after @section")
            title, label = _title_and_label(argument)
            title = title or argument
            current_subsection = Subsection(title=title, slug=_unique_slug(_slugify(title), used_slugs), label=label)
            current_section.subsections.append(current_subsection)
        elif command == "image":
            target = current_text or current_environment or current_subsection or current_section
            if target is None:
                raise ValueError("@image must appear after @section")
            image_group_id += 1
            target.content.extend(_parse_image_group(argument, image_group_id))
        elif command == "text":
            target = current_subsection or current_section
            if target is None:
                raise ValueError("@text must appear after @section")
            text_block = _parse_text(argument)
            target.content.append(text_block)
            current_text = text_block
        elif command == "label":
            target = current_text or current_environment or current_subsection or current_section
            if target is None:
                raise ValueError("@label must appear after @section")
            label = _strip_quotes(argument)
            if not label:
                raise ValueError("@label requires a label name")
            target.content.append(Label(name=label))
        elif command == "ref":
            target = current_text or current_environment or current_subsection or current_section
            if target is None:
                raise ValueError("@ref must appear after @section")
            values = _parse_key_values(argument)
            target.content.append(Reference(target=values.get("name", argument), text=values.get("text", "")))
        elif command in _ENVIRONMENTS:
            current_text = None
            target = current_subsection or current_section
            if target is None:
                raise ValueError(f"@{command} must appear after @section")
            title, label = _title_and_label(argument)
            environment = Environment(kind=command, title=title or (argument if command != "proof" else ""), label=label)
            target.content.append(environment)
            current_environment = environment
        elif command in _LIST_ENVIRONMENTS:
            target = current_text or current_environment or current_subsection or current_section
            if target is None:
                raise ValueError(f"@{command} must appear after @section")
            target.content.append(_parse_list(argument, ordered=(command == "enumerate")))
        elif command in {"relatedlinks", "relatedlink"}:
            values = _parse_key_values(argument)
            if "href" not in values:
                raise ValueError("@relatedlinks requires href = ...")
            document.related_links.append(RelatedLink(name=values.get("name", "Related link"), href=values["href"]))
        else:
            raise ValueError(f"Unknown Mark Two directive: @{command}")

        index = end_index + 1

    if display_math_lines is not None:
        raise ValueError("Unclosed display math block: expected \\]")
    return document


def parse_file(path: str | Path) -> Document:
    return parse(Path(path).read_text(encoding="utf-8"))
