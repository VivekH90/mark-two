"""Render a Mark Two Document into the HTML template."""

from html import escape
from pathlib import Path

from .ast import Document, Environment, Image, ListBlock, ListItem, MathBlock, Section


def _paragraphs(lines):
    if not lines: return ""
    paragraphs, current = [], []
    for line in lines:
        if line.strip(): current.append(line.strip())
        elif current:
            paragraphs.append(" ".join(current)); current = []
    if current: paragraphs.append(" ".join(current))
    return "\n".join(f"<p>{escape(p)}</p>" for p in paragraphs)


def _math_html(math: MathBlock) -> str:
    return f'<div class="math-display">\\[{math.content}\\]</div>'


def _image_html(image: Image) -> str:
    src = escape(image.src, quote=True); alt = escape(image.alt, quote=True)
    html = ['<figure class="article-image">', f'<img src="{src}" alt="{alt}" loading="lazy">']
    if image.caption: html.append(f'<figcaption>{escape(image.caption)}</figcaption>')
    html.append('</figure>')
    return "\n".join(html)


def _list_html(list_block: ListBlock, environment_counters) -> str:
    tag = "ol" if list_block.ordered else "ul"
    color = escape(list_block.color, quote=True)
    items = []
    for item in list_block.items:
        title_html = ""
        if item.title:
            title_html = f'<span class="list-item-title">{escape(item.title)}</span>'
        items.append(f'<li>{title_html}{_content_html(item.content, environment_counters)}</li>')
    return f'<{tag} class="mark-list" style="--list-color: {color};">\n{"\n".join(items)}\n</{tag}>'


def _environment_html(environment: Environment, number: int) -> str:
    kind = escape(environment.kind.lower()); label = environment.kind.capitalize()
    heading = f"{label} {number}"
    if environment.title: heading += f" ({escape(environment.title)})"
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
    section_color = escape(section.color, quote=True)
    html = [f'<section class="article-section" id="{escape(section.slug or "section")}" style="--section-color: {section_color};">', f'<h2><span class="section-symbol">§</span> {number}. {escape(section.title)}</h2>', _content_html(section.content, environment_counters)]
    for sub_number, subsection in enumerate(section.subsections, 1):
        html.extend([f'<section class="article-subsection" id="{escape(subsection.slug or "subsection")}">', f'<h3>{number}.{sub_number}. {escape(subsection.title)}</h3>', _content_html(subsection.content, environment_counters), '</section>'])
    html.append('</section>')
    return "\n".join(html)


def render(document: Document, template_path: str | Path) -> str:
    template = Path(template_path).read_text(encoding="utf-8")
    buttons = [f'<a class="nav-button" href="{escape(b.href, quote=True)}" style="--button-color: {escape(b.color, quote=True)};">{escape(b.name)}</a>' for b in document.buttons]
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
