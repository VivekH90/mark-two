"""Parser for the Mark Two article language."""

import re
from pathlib import Path
from typing import List

from .ast import (
    Button, Document, Environment, GallerySpec, Image, Label, ListBlock, ListItem,
    MathBlock, Reference, RelatedLink, Section, Subsection, TextBlock,
)

_DIRECTIVE_START = re.compile(r"^\s*@([A-Za-z][\w ]*)\s*\{")
_BLOCK_START = re.compile(r"^\s*@begin\s*\(\s*(.*?)\s*\)\s*(?:\{(.*)\})?\s*$", re.IGNORECASE)
_BLOCK_END = re.compile(r"^\s*@end\s*\(\s*([A-Za-z][\w-]*)\s*\)\s*$", re.IGNORECASE)
_ENVIRONMENTS = {"theorem","lemma","definition","corollary","axiom","proposition","remark","example","conjecture","notation","warning","proof"}
_LIST_ENVIRONMENTS = {"enumerate","itemize"}
_BLOCK_KINDS = {"section","subsection",*_ENVIRONMENTS,*_LIST_ENVIRONMENTS}
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



def _block_title_label(argument: str):
    values = _parse_key_values(argument)
    title = values.get("name", "")
    label = values.get("label", "")
    if not title and "=" not in argument:
        title = argument.strip()
    return title, label


def _parse_begin_header(inner: str, legacy_argument: str | None):
    """Parse LaTeX-like @begin(kind = Title, label = id) syntax.

    The older @begin(kind){...} form is accepted for compatibility.
    """
    if legacy_argument is not None:
        kind = inner.strip().lower()
        argument = legacy_argument.strip()
        return kind, argument

    parts = _split_top_level(inner)
    if not parts:
        raise ValueError("@begin(...) requires an environment name")

    first = parts[0].strip()
    match = re.fullmatch(r"([A-Za-z][\w-]*)\s*=\s*(.*)", first, re.DOTALL)
    if match:
        kind = match.group(1).lower()
        title = match.group(2).strip()
        argument_parts = []
        if title:
            argument_parts.append(f"name = {title}")
        argument_parts.extend(parts[1:])
        argument = ", ".join(argument_parts)
    else:
        kind = first.lower()
        argument = ", ".join(parts[1:]).strip()

    if not re.fullmatch(r"[a-z][a-z0-9_-]*", kind):
        raise ValueError(f"Invalid @begin environment name: {kind}")

    return kind, argument


def _parse_block_source(source: str) -> Document:
    """Parse the LaTeX-like enclosed-environment syntax."""
    document = Document()
    environment_stack = []
    current_section = None
    current_subsection = None
    pending = []
    used_slugs = set()
    lines = source.splitlines()
    index = 0
    math_lines = None

    def target():
        if environment_stack:
            return environment_stack[-1][1]
        return current_subsection or current_section

    def flush():
        item = target()
        text = "\n".join(pending).strip()
        pending.clear()
        if item is not None and text:
            item.content.append(TextBlock(text=text))

    def add_environment(kind, argument):
        if kind not in _ENVIRONMENTS and kind not in _LIST_ENVIRONMENTS:
            if kind in {"section", "subsection"}:
                raise ValueError(
                    f"Use @{kind}{{...}} for structural headings instead of @begin({kind}...)"
                )
            raise ValueError(f"Unknown block type: {kind}")

        parent = target()
        if parent is None or not hasattr(parent, "content"):
            raise ValueError(f"@begin({kind}...) must appear after @section{{...}}")

        if kind in _LIST_ENVIRONMENTS:
            values = _parse_key_values(argument)
            unknown = set(values) - {"color"}
            if unknown:
                raise ValueError(f"@begin({kind}, ...) only accepts color = ...")
            node = ListBlock(
                ordered=(kind == "enumerate"),
                color=values.get("color", "black"),
            )
        else:
            title, label = _block_title_label(argument)
            if not title and kind != "proof":
                raise ValueError(f"@begin({kind} = ...) requires an environment title")
            node = Environment(kind=kind, title=title, label=label)

        parent.content.append(node)
        environment_stack.append((kind, node))

    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()

        if math_lines is not None:
            if stripped == r"\]":
                flush()
                target_item = target()
                if target_item is None:
                    raise ValueError("display math must appear after @section")
                target_item.content.append(MathBlock("\n".join(math_lines)))
                math_lines = None
            else:
                math_lines.append(raw)
            index += 1
            continue

        if stripped == r"\[":
            flush()
            math_lines = []
            index += 1
            continue

        end_match = _BLOCK_END.match(raw)
        if end_match:
            flush()
            kind = end_match.group(1).lower()
            if not environment_stack:
                raise ValueError(f"@end({kind}) has no matching @begin(...)")
            actual = environment_stack[-1][0]
            if actual != kind:
                raise ValueError(f"Mismatched block: @end({kind}) closes @begin({actual})")
            environment_stack.pop()
            index += 1
            continue

        begin_match = _BLOCK_START.match(raw)
        if begin_match:
            flush()
            kind, argument = _parse_begin_header(
                begin_match.group(1),
                begin_match.group(2),
            )
            add_environment(kind, argument)
            index += 1
            continue

        directive = _extract_directive(lines, index)
        if directive:
            flush()
            command, argument, end_index = directive
            command = command.strip().lower().replace(" ", "")

            if command == "documenttitle":
                values = _parse_key_values(argument)
                document.document_tag = values.get("name", argument)
                document.banner = values.get("banner", "")
                document.banner_color = values.get("color", "")
            elif command == "folder":
                document.folder = argument
            elif command == "author":
                document.author = _parse_key_values(argument).get("name", argument)
            elif command == "date":
                document.date = argument
            elif command == "title":
                document.article_title = argument
            elif command == "tags":
                document.tags.extend(
                    [
                        _strip_quotes(x).strip()
                        for x in _split_top_level(argument)
                        if _strip_quotes(x).strip()
                    ]
                )
            elif command == "button":
                values = _parse_key_values(argument)
                document.buttons.append(
                    Button(
                        name=values.get("name", "Button"),
                        href=values.get("href", "#"),
                        color=values.get("color", "black"),
                    )
                )
            elif command == "gallery":
                values = _parse_key_values(argument)
                query = values.get("query", "").strip()
                if not query:
                    raise ValueError("@gallery requires query = ...")
                document.gallery = GallerySpec(
                    source=values.get("source", "NASA"),
                    query=query,
                    count=int(values.get("count", "7")),
                    seed=int(values["seed"]) if values.get("seed") else None,
                )
            elif command in {"relatedlinks", "relatedlink"}:
                values = _parse_key_values(argument)
                if "href" not in values:
                    raise ValueError("@relatedlinks requires href = ...")
                document.related_links.append(
                    RelatedLink(
                        name=values.get("name", "Related link"),
                        href=values["href"],
                    )
                )
            elif command == "section":
                if environment_stack:
                    raise ValueError("@section must not appear inside an open environment")
                title, label = _title_and_label(argument)
                title = title or argument.strip()
                if not title:
                    raise ValueError("@section requires a title")
                current_section = Section(
                    title=title,
                    slug=_unique_slug(_slugify(title), used_slugs),
                    label=label,
                )
                document.sections.append(current_section)
                current_subsection = None
            elif command == "subsection":
                if environment_stack:
                    raise ValueError("@subsection must not appear inside an open environment")
                if current_section is None:
                    raise ValueError("@subsection must appear after @section")
                title, label = _title_and_label(argument)
                title = title or argument.strip()
                if not title:
                    raise ValueError("@subsection requires a title")
                current_subsection = Subsection(
                    title=title,
                    slug=_unique_slug(_slugify(title), used_slugs),
                    label=label,
                )
                current_section.subsections.append(current_subsection)
            elif command == "image":
                target_item = target()
                if target_item is None:
                    raise ValueError("@image must appear after @section")
                image_group_id = getattr(target_item, "_mark_image_group_id", 0) + 1
                setattr(target_item, "_mark_image_group_id", image_group_id)
                target_item.content.extend(_parse_image_group(argument, image_group_id))
            elif command == "label":
                target_item = target()
                if target_item is None:
                    raise ValueError("@label must appear after @section")
                label = _strip_quotes(argument)
                if not label:
                    raise ValueError("@label requires a label name")
                target_item.content.append(Label(name=label))
            elif command == "ref":
                target_item = target()
                if target_item is None:
                    raise ValueError("@ref must appear after @section")
                values = _parse_key_values(argument)
                target_item.content.append(
                    Reference(
                        target=values.get("name", argument),
                        text=values.get("text", ""),
                    )
                )
            elif command in _ENVIRONMENTS:
                raise ValueError(
                    f"Use @begin({command} = ...) ... @end({command})"
                )
            elif command in _LIST_ENVIRONMENTS:
                target_item = target()
                if target_item is None:
                    raise ValueError(f"@{command} must appear after @section")
                target_item.content.append(
                    _parse_list(argument, ordered=(command == "enumerate"))
                )
            elif command == "text":
                raise ValueError("@text is no longer supported; write normal prose directly")
            else:
                raise ValueError(f"Unknown Mark Two directive: @{command}")

            index = end_index + 1
            continue

        if target() is not None:
            if stripped:
                pending.append(raw)
            else:
                flush()
            index += 1
            continue

        if stripped:
            raise ValueError("Text must appear after @section{{...}}")

        index += 1

    flush()
    if math_lines is not None:
        raise ValueError("Unclosed display math")
    if environment_stack:
        raise ValueError(
            f"Unclosed @begin({environment_stack[-1][0]}) environment"
        )
    return document

def parse(source: str) -> Document:
    if re.search(r"^\s*@(?:begin|end)\s*\(", source, re.IGNORECASE | re.MULTILINE):
        return _parse_block_source(source)
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
        if command in {"documenttitle", "author", "title", "button", "section", "subsection", "image", "gallery", "relatedlinks", "relatedlink", "text", "tags"}:
            current_environment = None
            current_text = None

        if command == "documenttitle":
            values = _parse_key_values(argument)
            document.document_tag = values.get("name", argument)
            document.banner = values.get("banner", "")
            document.banner_color = values.get("color", "")
        elif command == "gallery":
            values = _parse_key_values(argument)
            source = values.get("source", "NASA").strip()
            query = values.get("query", "").strip()
            count_raw = values.get("count", "7").strip()
            seed_raw = values.get("seed", "").strip()
            if not query:
                raise ValueError("@gallery requires query = ...")
            try:
                count = int(count_raw)
            except ValueError as exc:
                raise ValueError("@gallery count must be an integer") from exc
            if count < 1 or count > 20:
                raise ValueError("@gallery count must be between 1 and 20")
            seed = None
            if seed_raw:
                try:
                    seed = int(seed_raw)
                except ValueError as exc:
                    raise ValueError("@gallery seed must be an integer") from exc
            if source.lower() != "nasa":
                raise ValueError("Unsupported gallery source. Currently supported: NASA")
            document.gallery = GallerySpec(source=source, query=query, count=count, seed=seed)
        elif command == "author":
            values = _parse_key_values(argument)
            document.author = values.get("name", argument)
        elif command == "title":
            document.article_title = argument
        elif command == "tags":
            tags = [_strip_quotes(part).strip() for part in _split_top_level(argument) if _strip_quotes(part).strip()]
            document.tags.extend(tags)
        elif command == "button":
            values = _parse_key_values(argument)
            document.buttons.append(Button(name=values.get("name", "Button"), href=values.get("href", "#"), color=values.get("color", "black")))
        elif command == "section":
            values = _parse_key_values(argument)
            if "color" in values:
                raise ValueError("@section no longer supports color")
            title, label = _title_and_label(argument)
            title = title or argument
            current_section = Section(title=title, slug=_unique_slug(_slugify(title), used_slugs), label=label)
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
            raise ValueError("@text is no longer supported; write normal prose directly")
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
            raise ValueError(
                f"Use @begin({command} = ...) ... @end({command})"
            )
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
