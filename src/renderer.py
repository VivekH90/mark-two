"""Render a Mark Two Document into the HTML template."""

from html import escape
from pathlib import Path
import colorsys
import re

from .ast import Document, Environment, Image, Label, ListBlock, ListItem, MathBlock, Reference, Section

_CSS_COLOR_NAMES = {
    "black": "#000000", "white": "#ffffff", "red": "#ff0000", "green": "#008000", "blue": "#0000ff",
    "yellow": "#ffff00", "orange": "#ffa500", "purple": "#800080", "gray": "#808080", "grey": "#808080",
    "brown": "#a52a2a", "pink": "#ffc0cb", "teal": "#008080", "navy": "#000080", "maroon": "#800000",
    "olive": "#808000", "lime": "#00ff00", "cyan": "#00ffff", "magenta": "#ff00ff",
}


def _dark_mode_color(value: str) -> str:
    original = value.strip(); raw = _CSS_COLOR_NAMES.get(original.lower(), original.lower())
    match = re.fullmatch(r"#([0-9a-f]{6})", raw)
    if not match: return original
    r, g, b = [int(match.group(1)[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    if luminance >= 0.42: return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(hue, max(lightness, 0.45), saturation)
    return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"


def _inline_text(text: str, references) -> str:
    parts = re.split(r"(@ref\{[^{}]*\})", text)
    html = []
    for part in parts:
        match = re.fullmatch(r"@ref\{([^{}]*)\}", part.strip())
        if not match:
            html.append(escape(part))
            continue
        raw = match.group(1).strip()
        values = _parse_ref_argument(raw)
        target = values[0]
        custom_text = values[1]
        entry = references.get(target)
        if entry:
            href, label_text = entry
            html.append(f'<a class="cross-reference" href="{escape(href, quote=True)}">{escape(custom_text or label_text)}</a>')
        else:
            href = target if _looks_like_url(target) else f"#{escape(target, quote=True)}"
            html.append(f'<a class="cross-reference unresolved-reference" href="{escape(href, quote=True)}">{escape(custom_text or target)}</a>')
    return "".join(html)


def _looks_like_url(target: str) -> bool:
    return bool(re.match(r"^(?:https?://|/|(?:\.?\.?/)?[^#]+\.html(?:#.*)?$)", target, re.IGNORECASE)) or "#" in target


def _parse_ref_argument(argument: str):
    parts = []
    current = []
    quote = None
    depth = 0
    for char in argument:
        if char in {'"', "'"}:
            if quote == char: quote = None
            elif quote is None: quote = char
        elif quote is None:
            if char in "{[(": depth += 1
            elif char in "})]": depth = max(0, depth - 1)
            elif char == "," and depth == 0:
                parts.append("".join(current).strip()); current = []; continue
        current.append(char)
    parts.append("".join(current).strip())
    target = parts[0].strip('"\'') if parts else ""
    custom = ""
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            if key.strip().lower() == "text": custom = value.strip().strip('"\'')
    return target, custom


def _paragraphs(lines, references):
    if not lines: return ""
    paragraphs, current = [], []
    for line in lines:
        if line.strip(): current.append(line.strip())
        elif current: paragraphs.append(" ".join(current)); current = []
    if current: paragraphs.append(" ".join(current))
    return "\n".join(f"<p>{_inline_text(p, references)}</p>" for p in paragraphs)


def _math_html(math: MathBlock) -> str: return f'<div class="math-display">\\[{math.content}\\]</div>'


def _image_html(image: Image, references, figure_number=None) -> str:
    src = escape(image.src, quote=True); alt = escape(image.alt, quote=True)
    identifier = f' id="{escape(image.label, quote=True)}"' if image.label else ""
    size_style = []
    if image.width: size_style.append(f"width: {escape(image.width, quote=True)}")
    if image.height: size_style.append(f"height: {escape(image.height, quote=True)}")
    style = f' style="{"; ".join(size_style)}"' if size_style else ""
    html = [f'<figure class="article-image"{identifier}>', f'<img src="{src}" alt="{alt}" loading="lazy"{style}>']
    if image.caption: html.append(f'<figcaption>{escape(image.caption)}</figcaption>')
    html.append('</figure>'); return "\n".join(html)


def _list_html(list_block: ListBlock, environment_counters, references) -> str:
    tag = "ol" if list_block.ordered else "ul"; color = escape(list_block.color, quote=True); dark_color = escape(_dark_mode_color(list_block.color), quote=True)
    items = []
    for item in list_block.items:
        title_html = f'<span class="list-item-title">{escape(item.title)}</span>' if item.title else ""
        item_class = ' class="has-list-item-title"' if item.title else ""
        items.append(f'<li{item_class}>{title_html}{_content_html(item.content, environment_counters, references)}</li>')
    item_html = "\n".join(items)
    return f'<{tag} class="mark-list" style="--list-color: {color}; --list-color-dark: {dark_color};">\n{item_html}\n</{tag}>'


def _environment_html(environment: Environment, number: int, environment_counters, references) -> str:
    kind = escape(environment.kind.lower())
    if kind == "proof":
        identifier = f' id="{escape(environment.label, quote=True)}"' if environment.label else ""
        return f'<div class="proof-environment"{identifier}><div class="proof-heading">Proof</div><div class="proof-content">{_content_html(environment.content, environment_counters, references)}</div><div class="proof-qed" aria-label="Q.E.D.">□</div></div>'
    label = environment.kind.capitalize()
    heading = f'<span class="environment-label"><span class="environment-kind">{label}</span> <span class="environment-number">{number}</span></span>'
    if environment.title: heading += f' <span class="environment-title">({escape(environment.title)})</span>'
    identifier = f' id="{escape(environment.label, quote=True)}"' if environment.label else ""
    return f'<div class="math-environment {kind}"{identifier}><div class="environment-heading">{heading}</div><div class="environment-content">{_content_html(environment.content, environment_counters, references)}</div></div>'


def _content_html(items, environment_counters, references) -> str:
    html = []
    for item in items:
        if isinstance(item, Environment):
            environment_counters[item.kind] = environment_counters.get(item.kind, 0) + 1
            html.append(_environment_html(item, environment_counters[item.kind], environment_counters, references))
        elif isinstance(item, Image): html.append(_image_html(item, references))
        elif isinstance(item, MathBlock): html.append(_math_html(item))
        elif isinstance(item, ListBlock): html.append(_list_html(item, environment_counters, references))
        elif isinstance(item, Label): html.append(f'<span class="mark-label" id="{escape(item.name, quote=True)}"></span>')
        elif isinstance(item, Reference):
            target = item.target
            entry = references.get(target)
            if entry:
                href, label_text = entry
                text = item.text or label_text
            else:
                href = target if _looks_like_url(target) else f"#{escape(target, quote=True)}"
                text = item.text or target
            html.append(f'<p><a class="cross-reference" href="{escape(href, quote=True)}">{escape(text)}</a></p>')
        else: html.append(_paragraphs([item], references))
    return "\n".join(html)


def _build_reference_index(document: Document):
    references = {}
    counters = {}
    for number, section in enumerate(document.sections, 1):
        if section.label:
            references[section.label] = (f"#{section.slug or 'section'}", f"Section {number}")
        for sub_number, subsection in enumerate(section.subsections, 1):
            if subsection.label:
                references[subsection.label] = (f"#{subsection.slug or 'subsection'}", f"Subsection {number}.{sub_number}")
        for item in section.content + [content for subsection in section.subsections for content in subsection.content]:
            if isinstance(item, Environment):
                counters[item.kind] = counters.get(item.kind, 0) + 1
                if item.label:
                    references[item.label] = (f"#{item.label}", f"{item.kind.capitalize()} {counters[item.kind]}")
    return references


def _section_html(section: Section, number: int, environment_counters, references) -> str:
    section_color = escape(section.color, quote=True); dark_section_color = escape(_dark_mode_color(section.color), quote=True)
    identifier = escape(section.slug or "section", quote=True)
    html = [f'<section class="article-section" id="{identifier}" style="--section-color: {section_color}; --section-color-dark: {dark_section_color};">', f'<h2><span class="section-symbol">§</span> {number}. {escape(section.title)}</h2>', _content_html(section.content, environment_counters, references)]
    for sub_number, subsection in enumerate(section.subsections, 1):
        sub_identifier = escape(subsection.slug or "subsection", quote=True)
        html.extend([f'<section class="article-subsection" id="{sub_identifier}">', f'<h3>{number}.{sub_number}. {escape(subsection.title)}</h3>', _content_html(subsection.content, environment_counters, references), '</section>'])
    html.append('</section>'); return "\n".join(html)


def render(document: Document, template_path: str | Path) -> str:
    template = Path(template_path).read_text(encoding="utf-8")
    buttons = []
    for button in document.buttons:
        color = escape(button.color, quote=True); dark_color = escape(_dark_mode_color(button.color), quote=True)
        buttons.append(f'<a class="nav-button" href="{escape(button.href, quote=True)}" style="--button-color: {color}; --button-color-dark: {dark_color};">{escape(button.name)}</a>')
    if document.banner:
        banner_color = escape(document.banner_color or "#ffffff", quote=True)
        banner_dark_color = escape(_dark_mode_color(document.banner_color or "#ffffff"), quote=True)
        banner = f'<div class="site-banner"><img src="{escape(document.banner, quote=True)}" alt="" loading="eager"><a class="banner-title" href="#" style="--banner-title-color: {banner_color}; --banner-title-color-dark: {banner_dark_color};">{escape(document.document_title)}</a></div>'
    else: banner = f'<a class="document-title" href="#">{escape(document.document_title)}</a>'
    references = _build_reference_index(document)
    toc, article, environment_counters = [], [], {}
    for number, section in enumerate(document.sections, 1):
        toc.append(f'<li><a href="#{escape(section.slug or "section")}"><span class="toc-section-symbol">§</span> {number}. {escape(section.title)}</a>')
        if section.subsections:
            toc.append('<ol class="toc-subsections">')
            for sub_number, subsection in enumerate(section.subsections, 1): toc.append(f'<li><a href="#{escape(subsection.slug or "subsection")}">{number}.{sub_number}. {escape(subsection.title)}</a></li>')
            toc.append('</ol>')
        toc.append('</li>'); article.append(_section_html(section, number, environment_counters, references))
    related = [f'<li><a href="{escape(link.href, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(link.name)}</a></li>' for link in document.related_links]
    replacements = {"{{DOCUMENT_TITLE}}": escape(document.document_title), "{{ARTICLE_TITLE}}": escape(document.article_title), "{{BANNER}}": banner, "{{BUTTONS}}": "\n".join(buttons), "{{TOC}}": "\n".join(toc), "{{ARTICLE}}": "\n".join(article), "{{RELATED_LINKS}}": "\n".join(related)}
    for key, value in replacements.items(): template = template.replace(key, value)
    return template
