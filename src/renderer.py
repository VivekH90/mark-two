"""Render a Mark Two Document into the HTML template."""

from html import escape
from pathlib import Path
import colorsys
import re

from .ast import Document, Environment, Image, ListBlock, ListItem, MathBlock, Section

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


def _paragraphs(lines):
    if not lines: return ""
    paragraphs, current = [], []
    for line in lines:
        if line.strip(): current.append(line.strip())
        elif current: paragraphs.append(" ".join(current)); current = []
    if current: paragraphs.append(" ".join(current))
    return "\n".join(f"<p>{escape(p)}</p>" for p in paragraphs)


def _math_html(math: MathBlock) -> str: return f'<div class="math-display">\\[{math.content}\\]</div>'


def _image_html(image: Image) -> str:
    src = escape(image.src, quote=True); alt = escape(image.alt, quote=True)
    html = ['<figure class="article-image">', f'<img src="{src}" alt="{alt}" loading="lazy">']
    if image.caption: html.append(f'<figcaption>{escape(image.caption)}</figcaption>')
    html.append('</figure>'); return "\n".join(html)


def _list_html(list_block: ListBlock, environment_counters) -> str:
    tag = "ol" if list_block.ordered else "ul"; color = escape(list_block.color, quote=True); dark_color = escape(_dark_mode_color(list_block.color), quote=True)
    items = []
    for item in list_block.items:
        title_html = f'<span class="list-item-title">{escape(item.title)}</span>' if item.title else ""
        item_class = ' class="has-list-item-title"' if item.title else ""
        items.append(f'<li{item_class}>{title_html}{_content_html(item.content, environment_counters)}</li>')
    return f'<{tag} class="mark-list" style="--list-color: {color}; --list-color-dark: {dark_color};">\n{"\n".join(items)}\n</{tag}>'


def _environment_html(environment: Environment, number: int) -> str:
    kind = escape(environment.kind.lower())
    if kind == "proof":
        return f'<div class="proof-environment"><div class="proof-heading">Proof</div><div class="proof-content">{_content_html(environment.content, {})}</div><div class="proof-qed" aria-label="Q.E.D.">□</div></div>'
    label = environment.kind.capitalize(); heading = f'<span class="environment-label">{label}</span> <span class="environment-number">{number}</span>'
    if environment.title: heading += f' <span class="environment-title">({escape(environment.title)})</span>'
    return f'<div class="math-environment {kind}"><div class="environment-heading">{heading}</div><div class="environment-content">{_content_html(environment.content, {})}</div></div>'


def _content_html(items, environment_counters) -> str:
    html = []
    for item in items:
        if isinstance(item, Environment):
            environment_counters[item.kind] = environment_counters.get(item.kind, 0) + 1
            html.append(_environment_html(item, environment_counters[item.kind]))
        elif isinstance(item, Image): html.append(_image_html(item))
        elif isinstance(item, MathBlock): html.append(_math_html(item))
        elif isinstance(item, ListBlock): html.append(_list_html(item, environment_counters))
        else: html.append(_paragraphs([item]))
    return "\n".join(html)


def _section_html(section: Section, number: int, environment_counters) -> str:
    section_color = escape(section.color, quote=True); dark_section_color = escape(_dark_mode_color(section.color), quote=True)
    html = [f'<section class="article-section" id="{escape(section.slug or "section")}" style="--section-color: {section_color}; --section-color-dark: {dark_section_color};">', f'<h2><span class="section-symbol">§</span> {number}. {escape(section.title)}</h2>', _content_html(section.content, environment_counters)]
    for sub_number, subsection in enumerate(section.subsections, 1):
        html.extend([f'<section class="article-subsection" id="{escape(subsection.slug or "subsection")}">', f'<h3>{number}.{sub_number}. {escape(subsection.title)}</h3>', _content_html(subsection.content, environment_counters), '</section>'])
    html.append('</section>'); return "\n".join(html)


def render(document: Document, template_path: str | Path) -> str:
    template = Path(template_path).read_text(encoding="utf-8")
    buttons = []
    for button in document.buttons:
        color = escape(button.color, quote=True); dark_color = escape(_dark_mode_color(button.color), quote=True)
        buttons.append(f'<a class="nav-button" href="{escape(button.href, quote=True)}" style="--button-color: {color}; --button-color-dark: {dark_color};">{escape(button.name)}</a>')
    if document.banner:
        banner = f'<div class="site-banner"><img src="{escape(document.banner, quote=True)}" alt="" loading="eager"><a class="banner-title" href="#">{escape(document.document_title)}</a></div>'
    else: banner = f'<a class="document-title" href="#">{escape(document.document_title)}</a>'
    toc, article, environment_counters = [], [], {}
    for number, section in enumerate(document.sections, 1):
        toc.append(f'<li><a href="#{escape(section.slug or "section")}"><span class="toc-section-symbol">§</span> {number}. {escape(section.title)}</a>')
        if section.subsections:
            toc.append('<ol class="toc-subsections">')
            for sub_number, subsection in enumerate(section.subsections, 1): toc.append(f'<li><a href="#{escape(subsection.slug or "subsection")}">{number}.{sub_number}. {escape(subsection.title)}</a></li>')
            toc.append('</ol>')
        toc.append('</li>'); article.append(_section_html(section, number, environment_counters))
    related = [f'<li><a href="{escape(link.href, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(link.name)}</a></li>' for link in document.related_links]
    for key, value in {"{{DOCUMENT_TITLE}}":"", "{{ARTICLE_TITLE}}":escape(document.article_title), "{{BANNER}}":banner, "{{BUTTONS}}":"\n".join(buttons), "{{TOC}}":"\n".join(toc), "{{ARTICLE}}":"\n".join(article), "{{RELATED_LINKS}}":"\n".join(related)}.items(): template = template.replace(key, value)
    return template
