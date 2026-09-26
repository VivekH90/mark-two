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


def _navigation_icon(name: str) -> str:
    """Return a small inline icon for known site navigation buttons."""
    key = re.sub(r"\\s+", " ", name.strip().lower())
    icons = {
        "home": '<svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 10.8 12 3l9 7.8v9.2a1 1 0 0 1-1 1h-5.5v-6h-5v6H4a1 1 0 0 1-1-1z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M8.5 21v-6h7v6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
        "archives": '<svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A1.5 1.5 0 0 1 5.5 4h13A1.5 1.5 0 0 1 20 5.5v14A1.5 1.5 0 0 1 18.5 21h-13A1.5 1.5 0 0 1 4 19.5z" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8 4v17M8 8h7M11 12h5M11 16h5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
        "thoughts": '<svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M9.5 19.5c-1.7-.8-3-2-3.6-3.7C5.2 14.7 5 13.4 5 12a7 7 0 1 1 14 0c0 1.4-.2 2.7-.9 3.8-.6 1.3-1.4 2.5-2.8 3.7H9.5Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M9 21h6M9.5 17.5h5M9.7 11.5c.7-.9 1.5-.9 2.3 0 .7-.9 1.5-.9 2.3 0 .5.6.9 1.2.8 2M12 8.5v3" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>',
        "github": '<svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 .7a11.3 11.3 0 0 0-3.6 22c.6.1.8-.3.8-.6v-2.1c-3.1.7-3.8-1.3-3.8-1.3-.5-1.3-1.2-1.6-1.2-1.6-1-.7.1-.7.1-.7 1.1.1 1.7 1.1 1.7 1.1 1 .1 1.5-.7 1.8-1.1.1-.7.4-1.1.6-1.4-2.5-.3-5.2-1.2-5.2-5.6 0-1.2.4-2.2 1.1-3-.1-.3-.5-1.5.1-3 0 0 .9-.3 3.1 1.1a10.7 10.7 0 0 1 5.6 0c2.2-1.4 3.1-1.1 3.1-1.1.6 1.5.2 2.7.1 3 .7.8 1.1 1.8 1.1 3 0 4.4-2.7 5.3-5.2 5.6.4.3.7.9.7 1.8v2.7c0 .3.2.7.8.6A11.3 11.3 0 0 0 12 .7Z"/></svg>'
    }
    return icons.get(key, "")


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
    return "\n".join(f"<p>{_inline_text(p, references)}</p>" for p in paragraphs)


def _text_html(text: TextBlock, references, environment_counters, figure_counter) -> str:
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
    content = _content_html(text.content, environment_counters, references, figure_counter, 0)
    if content:
        return f'<div class="text-environment">{text_html}<div class="text-content">{content}</div></div>'
    return f'<div class="text-environment">{text_html}</div>'


def _math_html(math: MathBlock) -> str:
    return f'<div class="math-display">\\[{math.content}\\]</div>'


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



def _list_html(list_block: ListBlock, environment_counters, references, figure_counter, depth: int) -> str:
    tag = "ol" if list_block.ordered else "ul"
    type_attr = ' type="a"' if list_block.ordered and depth > 0 else ""
    color = escape(list_block.color, quote=True)
    dark_color = escape(_dark_mode_color(list_block.color), quote=True)
    items = []
    for item in list_block.items:
        title_html = f'<span class="list-item-title">{escape(item.title)}</span>' if item.title else ""
        item_class = ' class="has-list-item-title"' if item.title else ""
        content = _content_html(item.content, environment_counters, references, figure_counter, depth + 1)
        items.append(f"<li{item_class}>{title_html}{content}</li>")
    return f'<{tag} class="mark-list"{type_attr} style="--list-color: {color}; --list-color-dark: {dark_color};">\n' + "\n".join(items) + f"\n</{tag}>"


def _environment_html(environment: Environment, number: int, environment_counters, references, figure_counter) -> str:
    kind = environment.kind.strip().lower()
    identifier = f' id="{escape(environment.label, quote=True)}"' if environment.label else ""
    content = _content_html(environment.content, environment_counters, references, figure_counter, 0)

    if kind == "proof":
        return (
            f'<div class="box proof"{identifier}>'
            '<div class="label">Proof</div>'
            f'<div class="proof-content">{content}</div>'
            '<div class="qed" aria-label="Q.E.D.">□</div>'
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


def _content_html(items, environment_counters, references, figure_counter, list_depth: int = 0) -> str:
    html = []
    index = 0
    while index < len(items):
        item = items[index]
        if isinstance(item, Environment):
            environment_counters[item.kind] = environment_counters.get(item.kind, 0) + 1
            html.append(_environment_html(item, environment_counters[item.kind], environment_counters, references, figure_counter))
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
            html.append(_text_html(item, references, environment_counters, figure_counter))
        elif isinstance(item, ListBlock):
            html.append(_list_html(item, environment_counters, references, figure_counter, list_depth))
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
    references, counters = {}, {}
    for number, section in enumerate(document.sections, 1):
        if section.label:
            references[section.label] = (f"#{section.slug or 'section'}", f"Section {number}")
        for sub_number, subsection in enumerate(section.subsections, 1):
            if subsection.label:
                references[subsection.label] = (f"#{subsection.slug or 'subsection'}", f"Subsection {number}.{sub_number}")
        content = list(section.content)
        for subsection in section.subsections:
            content.extend(subsection.content)
        for item in content:
            if isinstance(item, Environment):
                counters[item.kind] = counters.get(item.kind, 0) + 1
                if item.label:
                    references[item.label] = (f"#{item.label}", f"{item.kind.capitalize()} {counters[item.kind]}")
    return references


def _section_html(section: Section, number: int, environment_counters, references, figure_counter) -> str:
    identifier = escape(section.slug or "section", quote=True)
    html = [
        f'<section class="article-section" id="{identifier}">',
        f'<h2><span class="num">{number}</span>{escape(section.title)}</h2>',
        _content_html(section.content, environment_counters, references, figure_counter),
    ]
    for sub_number, subsection in enumerate(section.subsections, 1):
        sub_identifier = escape(subsection.slug or "subsection", quote=True)
        html.extend([
            f'<section class="article-subsection" id="{sub_identifier}">',
            f'<h3><span class="num">{number}.{sub_number}</span>{escape(subsection.title)}</h3>',
            _content_html(subsection.content, environment_counters, references, figure_counter),
            "</section>",
        ])
    html.append("</section>")
    return "\n".join(html)



def _gallery_html(document: Document) -> str:
    if not document.gallery_items:
        return ""
    items = []
    for item in document.gallery_items:
        title = escape(item.title or "Image", quote=True)
        alt = escape(item.alt or item.title or "Image", quote=True)
        url = escape(item.url, quote=True)
        full_url = escape(item.source_url or item.url, quote=True)
        caption = escape(item.title or item.credit or "Image", quote=True)
        items.append(
            f'<button class="thumb" type="button" data-full="{full_url}" data-title="{title}" data-caption="{caption}" aria-label="Open {title}">'
            f'<img src="{url}" alt="{alt}" loading="lazy" referrerpolicy="no-referrer"></button>'
        )
    return '<div class="strip" id="nasa-gallery" aria-label="Article image gallery">' + "".join(items) + '</div>'



def _breadcrumb_html(document: Document) -> str:
    github_href = "https://github.com"
    home_href = "/"
    for button in document.buttons:
        key = button.name.strip().lower()
        if key == "github":
            github_href = button.href
        elif key == "home":
            home_href = button.href
    chunks = [
        f'<a href="{escape(home_href, quote=True)}">Home</a>',
        '<span class="sep">›</span>',
    ]
    if document.document_tag:
        chunks.extend([f'<a href="#">{escape(document.document_tag)}</a>', '<span class="sep">›</span>'])
    if document.folder:
        chunks.extend([f'<a href="#">{escape(document.folder)}</a>', '<span class="sep">›</span>'])
    chunks.append(f'<span class="current">{escape(document.article_title)}</span>')
    icon_html = (
        '<a href="' + escape(home_href, quote=True) + '" aria-label="Home" title="Home">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 11l9-7 9 7"/><path d="M5 10v9h14v-9"/></svg></a>'
        '<a href="' + escape(github_href, quote=True) + '" aria-label="GitHub" title="GitHub">'
        '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.58 2 12.17c0 4.49 2.87 8.3 6.84 9.65.5.1.68-.22.68-.49 0-.24-.01-1.03-.01-1.87-2.79.61-3.38-1.22-3.38-1.22-.46-1.19-1.11-1.5-1.11-1.5-.9-.63.07-.62.07-.62 1 .07 1.53 1.05 1.53 1.05.89 1.55 2.34 1.1 2.91.84.09-.66.35-1.1.63-1.35-2.23-.26-4.57-1.14-4.57-5.06 0-1.12.39-2.03 1.03-2.75.1-.26-.45-1.3.1-2.7 0 0 .84-.27 2.75 1.05a9.3 9.3 0 0 1 5 0c1.91-1.32 2.75-1.05 2.75-1.05.55 1.4.2 2.44.1 2.7-.64.72-1.03 1.63-1.03 2.75 0 3.93 2.34 4.79 4.58 5.05-.36.32-.68.94-.68 1.9v2.81c0 .34.18.6.69.49A10.02 10.02 0 0 0 22 12.17C22 6.58 17.52 2 12 2z"/></svg></a>'
        '<button class="theme-toggle" type="button" aria-label="Toggle dark mode" title="Toggle dark mode">'
        '<svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2.2M12 19.8V22M4.2 4.2l1.6 1.6M18.2 18.2l1.6 1.6M2 12h2.2M19.8 12H22M4.2 19.8l1.6-1.6M18.2 5.8l1.6-1.6"/></svg>'
        '<svg class="moon" viewBox="0 0 24 24" fill="currentColor"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"/></svg>'
        '</button>'
    )
    date_html = f'<time>{escape(document.date)}</time>' if document.date else ""
    return (
        '<div class="metabar"><nav class="crumbs">' + "".join(chunks) +
        '</nav><div class="icons">' + icon_html + '</div></div>'
    )




def render(document: Document, template_path: str | Path) -> str:
    template = Path(template_path).read_text(encoding="utf-8")

    buttons = []
    for button in document.buttons:
        buttons.append(
            f'<li><a href="{escape(button.href, quote=True)}">{escape(button.name)}</a></li>'
        )

    references = _build_reference_index(document)
    toc, article, environment_counters = [], [], {}
    figure_counter = {"number": 0}

    for number, section in enumerate(document.sections, 1):
        section_id = escape(section.slug or "section", quote=True)
        toc.append(
            f'<li><a href="#{section_id}">{number}. {escape(section.title)}</a></li>'
        )
        for sub_number, subsection in enumerate(section.subsections, 1):
            subsection_id = escape(subsection.slug or "subsection", quote=True)
            toc.append(
                f'<li class="sub"><a href="#{subsection_id}">'
                f'{number}.{sub_number}. {escape(subsection.title)}</a></li>'
            )
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
        "{{GALLERY}}": _gallery_html(document),
        "{{ARTICLE_TITLE}}": escape(document.article_title),
        "{{AUTHOR}}": escape(document.author),
        "{{ARTICLE_DATE_META}}": date_meta,
        "{{ARTICLE_SECTION_LABEL}}": section_label,
        "{{TAGS}}": tag_block,
        "{{BREADCRUMB}}": _breadcrumb_html(document),
        "{{BUTTONS}}": "\n".join(buttons),
        "{{TOC}}": "\n".join(toc),
        "{{ARTICLE}}": "\n".join(article),
        "{{RELATED_LINKS}}": "\n".join(related),
    }

    for key, value in replacements.items():
        template = template.replace(key, value)
    return template
