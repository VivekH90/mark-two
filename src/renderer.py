"""Render a Mark Two Document into the HTML template."""

from html import escape
from pathlib import Path
import colorsys
import re

from .ast import Document, Environment, Image, Label, ListBlock, MathBlock, Reference, Section, TextBlock

_CSS_COLOR_NAMES = {
    "black": "#000000", "white": "#ffffff", "red": "#ff0000", "green": "#008000",
    "blue": "#0000ff", "yellow": "#ffff00", "orange": "#ffa500", "purple": "#800080",
    "gray": "#808080", "grey": "#808080", "brown": "#a52a2a", "pink": "#ffc0cb",
    "teal": "#008080", "navy": "#000080", "maroon": "#800000", "olive": "#808000",
    "lime": "#00ff00", "cyan": "#00ffff", "magenta": "#ff00ff",
}


def _dark_mode_color(value: str) -> str:
    original = value.strip()
    raw = _CSS_COLOR_NAMES.get(original.lower(), original.lower())
    match = re.fullmatch(r"#([0-9a-f]{6})", raw)
    if not match:
        return original
    r, g, b = [int(match.group(1)[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    if luminance >= 0.42:
        return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(hue, max(lightness, 0.45), saturation)
    return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"


def _parse_ref_argument(argument: str):
    parts, current, quote, depth = [], [], None, 0
    escaped = False
    for char in argument:
        if escaped:
            escaped = False
            current.append(char)
            continue
        if char == "\\":
            escaped = True
            current.append(char)
            continue
        if char in "\"'":
            quote = None if quote == char else char if quote is None else quote
        elif quote is None:
            if char in "{[(":
                depth += 1
            elif char in "})]":
                depth = max(0, depth - 1)
            elif char == "," and depth == 0:
                parts.append("".join(current).strip())
                current = []
                continue
        current.append(char)
    parts.append("".join(current).strip())
    target = parts[0].strip('"\'') if parts else ""
    custom = ""
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            if key.strip().lower() == "text":
                custom = value.strip().strip('"\'')
    return target, custom


def _split_top_level(argument: str):
    parts, current, quote, depth = [], [], None, 0
    escaped = False
    for char in argument:
        if escaped:
            escaped = False
            current.append(char)
            continue
        if char == "\\":
            escaped = True
            current.append(char)
            continue
        if char in "\"'":
            quote = None if quote == char else char if quote is None else quote
        elif quote is None:
            if char in "{[(":
                depth += 1
            elif char in "})]":
                depth = max(0, depth - 1)
            elif char == "," and depth == 0:
                parts.append("".join(current).strip())
                current = []
                continue
        current.append(char)
    parts.append("".join(current).strip())
    return parts


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _parse_key_value_fields(argument: str):
    fields = {}
    for part in _split_top_level(argument):
        if "=" in part:
            key, value = part.split("=", 1)
            fields[key.strip().lower()] = _strip_quotes(value)
    return fields


def _extract_inline_block(text: str, start: int):
    brace = text.find("{", start)
    if brace == -1:
        return None
    depth, quote, escaped = 0, None, False
    for i in range(brace, len(text)):
        char = text[i]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in "\"'":
            quote = None if quote == char else char if quote is None else quote
            continue
        if quote is not None:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[brace + 1:i], i + 1
    return None


def _looks_like_url(target: str) -> bool:
    return bool(re.match(r"^(?:https?://|/|(?:\.?\.?/)?[^#]+\.html(?:#.*)?$)", target, re.IGNORECASE)) or "#" in target


def _split_inline_color(argument: str):
    fields = _parse_key_value_fields(argument)
    color = fields.get("color") or fields.get("colour")
    content = fields.get("text")
    if content is None:
        content = fields.get("content")
    if color is not None and content is not None:
        return color, content
    parts = _split_top_level(argument)
    if len(parts) >= 2:
        return _strip_quotes(parts[0]), ",".join(parts[1:]).strip()
    return "", argument


def _safe_color(value: str) -> bool:
    value = value.strip()
    return bool(
        re.fullmatch(r"#[0-9a-fA-F]{3,8}", value)
        or re.fullmatch(r"(?:rgb|rgba|hsl|hsla)\([^{};]*\)", value, re.IGNORECASE)
        or re.fullmatch(r"[a-zA-Z]+", value)
    )


def _inline_text(text: str, references) -> str:
    output = []
    i = 0
    commands = ("ref", "bold", "italic", "color")
    while i < len(text):
        command = next((name for name in commands if text.startswith(f"@{name}{{", i)), None)
        if command:
            extracted = _extract_inline_block(text, i)
            if extracted is not None:
                argument, end = extracted
                if command == "bold":
                    output.append(f"<strong>{_inline_text(argument, references)}</strong>")
                elif command == "italic":
                    output.append(f"<em>{_inline_text(argument, references)}</em>")
                elif command == "color":
                    color, content = _split_inline_color(argument)
                    if color and _safe_color(color):
                        dark = _dark_mode_color(color)
                        output.append(f'<span class="inline-color" style="--inline-color: {escape(color, quote=True)}; --inline-color-dark: {escape(dark, quote=True)}">{_inline_text(content, references)}</span>')
                    else:
                        output.append(escape(text[i:end]))
                else:
                    target, custom_text = _parse_ref_argument(argument.strip())
                    entry = references.get(target)
                    if entry:
                        href, label_text = entry
                        output.append(f'<a class="cross-reference" href="{escape(href, quote=True)}">{escape(custom_text or label_text)}</a>')
                    else:
                        href = target if _looks_like_url(target) else f"#{escape(target, quote=True)}"
                        output.append(f'<a class="cross-reference unresolved-reference" href="{escape(href, quote=True)}">{escape(custom_text or target)}</a>')
                i = end
                continue
        j = text.find("@", i + 1)
        if j == -1:
            j = len(text)
        output.append(escape(text[i:j]))
        i = j
    return "".join(output)


def _paragraphs(lines, references):
    if not lines:
        return ""
    paragraphs, current = [], []
    for line in lines:
        if line.strip():
            current.append(line.strip())
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    rendered = []
    for paragraph in paragraphs:
        if re.match(r"^Running example:\s*", paragraph, re.IGNORECASE):
            rest = re.sub(r"^Running example:\s*", "", paragraph, count=1, flags=re.IGNORECASE)
            rendered.append(f'<p class="proto">Running example: <i>{_inline_text(rest, references)}</i></p>')
        else:
            rendered.append(f"<p>{_inline_text(paragraph, references)}</p>")
    return "\n".join(rendered)


def _text_html(text: TextBlock, references, environment_counters, figure_counter, section_number=None) -> str:
    styles = []
    if text.bold:
        styles.append("font-weight: 700")
    if text.italic:
        styles.append("font-style: italic")
    if text.color and _safe_color(text.color):
        styles.append(f"--text-color: {escape(text.color, quote=True)}")
        styles.append(f"--text-color-dark: {escape(_dark_mode_color(text.color), quote=True)}")
    style = f' style="{"; ".join(styles)}"' if styles else ""
    text_html = f'<p class="mark-text"{style}>{_inline_text(text.text, references)}</p>'
    content = _content_html(text.content, environment_counters, references, figure_counter, 0, section_number)
    if content:
        return f'<div class="text-environment">{text_html}<div class="text-content">{content}</div></div>'
    return f'<div class="text-environment">{text_html}</div>'


def _math_html(math: MathBlock) -> str:
    # Escape TeX before embedding it in HTML so characters such as <, >, and &
    # cannot be interpreted as HTML markup. The browser decodes these entities
    # before MathJax sees the text, preserving the original TeX expression.
    return f'<div class="math-display">\\[{escape(math.content)}\\]</div>'


def _image_tag(image: Image, extra_style: str = "") -> str:
    styles = []
    if image.width:
        styles.append(f"width: {escape(image.width, quote=True)}")
    if image.height and image.height.lower() != "auto":
        styles.append(f"height: {escape(image.height, quote=True)}")
    if extra_style:
        styles.append(extra_style)
    style = f' style="{"; ".join(styles)}"' if styles else ""
    return f'<img src="{escape(image.src, quote=True)}" alt="{escape(image.alt, quote=True)}" loading="lazy"{style}>'


def _caption_html(caption: str, figure_number: int) -> str:
    return f'<figcaption><strong>Figure {figure_number}:</strong> {escape(caption)}</figcaption>'


def _image_html(image: Image, figure_number: int) -> str:
    identifier = f' id="{escape(image.label, quote=True)}"' if image.label else ""
    html = [f'<figure class="diagram"{identifier}>', _image_tag(image)]
    if image.caption:
        html.append(_caption_html(image.caption, figure_number))
    html.append("</figure>")
    return "\n".join(html)


def _multi_image_html(images, figure_number: int) -> str:
    identifier = f' id="{escape(images[0].label, quote=True)}"' if images[0].label else ""
    image_html = []
    for image in images:
        extra = "width: 100%; height: auto; object-fit: contain; margin: 0;"
        image_html.append(_image_tag(image, extra))
    html = [f'<figure class="diagram"{identifier}>',
            '<div class="image-row" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(0,1fr));gap:10px;">',
            "\n".join(image_html), "</div>"]
    if images[0].caption:
        html.append(_caption_html(images[0].caption, figure_number))
    html.append("</figure>")
    return "\n".join(html)



def _list_html(list_block: ListBlock, environment_counters, references, figure_counter, depth: int, section_number=None) -> str:
    tag = "ol" if list_block.ordered else "ul"
    type_attr = ' type="a"' if list_block.ordered and depth > 0 else ""
    color = escape(list_block.color, quote=True)
    dark_color = escape(_dark_mode_color(list_block.color), quote=True)
    items = []
    for item in list_block.items:
        title_html = f'<span class="list-item-title">{escape(item.title)}</span>' if item.title else ""
        item_class = ' class="has-list-item-title"' if item.title else ""
        content = _content_html(item.content, environment_counters, references, figure_counter, depth + 1, section_number)
        items.append(f"<li{item_class}>{title_html}{content}</li>")
    return f'<{tag} class="mark-list"{type_attr} style="--list-color: {color}; --list-color-dark: {dark_color};">\n' + "\n".join(items) + f"\n</{tag}>"


def _environment_html(environment: Environment, number: int, environment_counters, references, figure_counter, section_number=None) -> str:
    kind = environment.kind.strip().lower()
    identifier = f' id="{escape(environment.label, quote=True)}"' if environment.label else ""
    content = _content_html(environment.content, environment_counters, references, figure_counter, 0, section_number)

    if kind == "colourbox":
        return (
            f'<div class="box colourbox"{identifier}>'
            f'<div class="box-content">{content}</div>'
            '</div>'
        )

    if kind == "proof":
        return (
            f'<div class="box proof"{identifier}>'
            '<div class="label">Proof</div>'
            f'<div class="proof-content">{content}</div>'
            '<div class="qed" aria-label="Q.E.D.">□</div>'
            '</div>'
        )

    if kind == "conclusion":
        return (
            f'<div class="box conclusion"{identifier}>'
            '<div class="label">Conclusion</div>'
            f'<div class="box-content">{content}</div>'
            '</div>'
        )

    label = kind.capitalize()
    label_text = f"{label} {number}"
    if environment.title:
        label_text += f" — {escape(environment.title)}"

    return (
        f'<div class="box {escape(kind, quote=True)}"{identifier}>'
        f'<div class="label">{label_text}</div>'
        f'<div class="box-content">{content}</div>'
        '</div>'
    )


def _content_html(items, environment_counters, references, figure_counter, list_depth: int = 0, section_number: int | None = None) -> str:
    html = []
    index = 0
    while index < len(items):
        item = items[index]
        if isinstance(item, Environment):
            if item.kind.strip().lower() in {"proof", "conclusion", "colourbox"}:
                number = ""
            else:
                environment_counters["__item__"] = environment_counters.get("__item__", 0) + 1
                item_number = environment_counters["__item__"]
                number = f"{section_number}.{item_number}" if section_number is not None else str(item_number)
            html.append(_environment_html(item, number, environment_counters, references, figure_counter, section_number))
        elif isinstance(item, Image):
            group = [item]
            next_index = index + 1
            while next_index < len(items) and isinstance(items[next_index], Image) and items[next_index].group == item.group:
                group.append(items[next_index])
                next_index += 1
            figure_counter["number"] += 1
            html.append(_image_html(group[0], figure_counter["number"]) if len(group) == 1 else _multi_image_html(group, figure_counter["number"]))
            index = next_index - 1
        elif isinstance(item, MathBlock):
            html.append(_math_html(item))
        elif isinstance(item, TextBlock):
            html.append(_text_html(item, references, environment_counters, figure_counter, section_number))
        elif isinstance(item, ListBlock):
            html.append(_list_html(item, environment_counters, references, figure_counter, list_depth, section_number))
        elif isinstance(item, Label):
            html.append(f'<span class="mark-label" id="{escape(item.name, quote=True)}"></span>')
        elif isinstance(item, Reference):
            entry = references.get(item.target)
            if entry:
                href, label_text = entry
                text = item.text or label_text
            else:
                href = item.target if _looks_like_url(item.target) else f"#{escape(item.target, quote=True)}"
                text = item.text or item.target
            html.append(f'<p><a class="cross-reference" href="{escape(href, quote=True)}">{escape(text)}</a></p>')
        else:
            html.append(_paragraphs([item], references))
        index += 1
    return "\n".join(html)


def _build_reference_index(document: Document):
    references = {}
    for number, section in enumerate(document.sections, 1):
        item_number = 0
        if section.label:
            references[section.label] = (f"#{section.slug or 'section'}", f"Section {number}")
        for sub_number, subsection in enumerate(section.subsections, 1):
            if subsection.label:
                references[subsection.label] = (f"#{subsection.slug or 'subsection'}", f"Subsection {number}.{sub_number}")
        content = list(section.content)
        for subsection in section.subsections:
            content.extend(subsection.content)
        for item in content:
            if isinstance(item, Environment) and item.kind.strip().lower() not in {"proof", "conclusion"}:
                item_number += 1
                if item.label:
                    references[item.label] = (f"#{item.label}", f"{item.kind.capitalize()} {number}.{item_number}")
    return references


def _section_html(section: Section, number: int, environment_counters, references, figure_counter) -> str:
    identifier = escape(section.slug or "section", quote=True)
    environment_counters["__item__"] = 0
    html = [
        f'<section class="article-section">',
        f'<h2 id="{identifier}"><span class="section-number">§{number}</span><span class="section-title">{escape(section.title)}</span></h2>',
        _content_html(section.content, environment_counters, references, figure_counter, section_number=number),
    ]
    for sub_number, subsection in enumerate(section.subsections, 1):
        sub_identifier = escape(subsection.slug or "subsection", quote=True)
        html.extend([
            f'<section class="article-subsection">',
            f'<h3 id="{sub_identifier}"><span class="section-number">§{number}.{sub_number}</span><span class="section-title">{escape(subsection.title)}</span></h3>',
            _content_html(subsection.content, environment_counters, references, figure_counter, section_number=number),
            "</section>",
        ])
    html.append("</section>")
    return "\n".join(html)



def render(document: Document, template_path: str | Path) -> str:
    template = Path(template_path).read_text(encoding="utf-8")

    buttons = []
    for button in document.buttons:
        color = escape(button.color or "black", quote=True)
        buttons.append(
            f'<li><a href="{escape(button.href, quote=True)}" style="--button-color: {color};">{escape(button.name)}</a></li>'
        )

    references = _build_reference_index(document)
    article, environment_counters = [], {}
    figure_counter = {"number": 0}

    for number, section in enumerate(document.sections, 1):
        article.append(_section_html(section, number, environment_counters, references, figure_counter))

    related = [
        f'<li><a href="{escape(link.href, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(link.name)}</a></li>'
        for link in document.related_links
    ]

    tag_items = [f'<span>{escape(tag)}</span>' for tag in document.tags]
    tag_block = f'<div class="tags">{"".join(tag_items)}</div>' if tag_items else ""
    date_meta = f'<span>·</span><time>{escape(document.date)}</time>' if document.date else ""
    section_label = escape(document.folder or document.document_tag or "Reading")

    replacements = {
        "{{ARTICLE_TITLE}}": escape(document.article_title),
        "{{ARTICLE_DESCRIPTION}}": escape(document.description),
        "{{AUTHOR}}": escape(document.author),
        "{{ARTICLE_DATE_META}}": date_meta,
        "{{ARTICLE_SECTION_LABEL}}": section_label,
        "{{TAGS}}": tag_block,
        "{{BUTTONS}}": "\n".join(buttons),
        "{{ARTICLE}}": "\n".join(article),
        "{{RELATED_LINKS}}": "\n".join(related),
    }

    for key, value in replacements.items():
        template = template.replace(key, value)
    return template
