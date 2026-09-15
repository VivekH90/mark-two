"""Render a Mark Two Document into the HTML template."""

from html import escape
from pathlib import Path

from .ast import Document, Environment, Image, ListBlock, MathBlock, Section


def _paragraphs(lines):
    if not lines:
        return ""
    paragraphs = []
    current = []
    for line in lines:
        if line.strip():
            current.append(line.strip())
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    return "\n".join(f"<p>{escape(p)}</p>" for p in paragraphs)


def _math_html(math: MathBlock) -> str:
    return f'<div class="math-display">\\[{math.content}\\]</div>'


def _image_html(image: Image) -> str:
    src = escape(image.src, quote=True)
    alt = escape(image.alt, quote=True)
    html = ['<figure class="article-image">', f'<img src="{src}" alt="{alt}" loading="lazy">']
    if image.caption:
        html.append(f'<figcaption>{escape(image.caption)}</figcaption>')
    html.append('</figure>')
    return "\n".join(html)


def _list_html(list_block: ListBlock) -> str:
    tag = "ol" if list_block.ordered else "ul"
    color = escape(list_block.color, quote=True)
    items = "\n".join(f"<li>{item}</li>" for item in list_block.items)
    return f'<{tag} class="mark-list" style="--list-color: {color};">\n{items}\n</{tag}>'


def _environment_html(environment: Environment, number: int) -> str:
    kind = escape(environment.kind.lower())
    label = environment.kind.capitalize()
    heading = f"{label} {number}"
    if environment.title:
        heading += f" ({escape(environment.title)})"
    return (
        f'<div class="math-environment {kind}">'
        f'<div class="environment-heading">{heading}</div>'
        f'<div class="environment-content">{_content_html(environment.content, {})}</div>'
        f"</div>"
    )


def _content_html(items, environment_counters) -> str:
    html = []
    for item in items:
        if isinstance(item, Environment):
            environment_counters[item.kind] = environment_counters.get(item.kind, 0) + 1
            html.append(_environment_html(item, environment_counters[item.kind]))
        elif isinstance(item, Image):
            html.append(_image_html(item))
        elif isinstance(item, MathBlock):
            html.append(_math_html(item))
        elif isinstance(item, ListBlock):
            html.append(_list_html(item))
        else:
            html.append(_paragraphs([item]))
    return "\n".join(html)


def _section_html(section: Section, number: int, environment_counters) -> str:
    section_color = escape(section.color, quote=True)
    html = [f'<section class="article-section" id="{escape(section.slug or "section")}" style="--section-color: {section_color};">']
    html.append(f'<h2><span class="section-symbol">§</span> {number}. {escape(section.title)}</h2>')
    html.append(_content_html(section.content, environment_counters))
    for sub_number, subsection in enumerate(section.subsections, 1):
        html.append(f'<section class="article-subsection" id="{escape(subsection.slug or "subsection")}">')
        html.append(f'<h3>{number}.{sub_number}. {escape(subsection.title)}</h3>')
        html.append(_content_html(subsection.content, environment_counters))
        html.append("</section>")
    html.append("</section>")
    return "\n".join(html)


def render(document: Document, template_path: str | Path) -> str:
    template = Path(template_path).read_text(encoding="utf-8")
    buttons = []
    for button in document.buttons:
        color = escape(button.color, quote=True)
        buttons.append(f'<a class="nav-button" href="{escape(button.href, quote=True)}" style="--button-color: {color};">{escape(button.name)}</a>')

    if document.banner:
        banner_src = escape(document.banner, quote=True)
        banner = f'<div class="site-banner"><img src="{banner_src}" alt="" loading="eager"><a class="banner-title" href="#">{escape(document.document_title)}</a></div>'
    else:
        banner = f'<a class="document-title" href="#">{escape(document.document_title)}</a>'

    toc = []
    article = []
    environment_counters = {}
    for number, section in enumerate(document.sections, 1):
        toc.append(f'<li><a href="#{escape(section.slug or "section")}"><span class="toc-section-symbol">§</span> {number}. {escape(section.title)}</a>')
        if section.subsections:
            toc.append('<ol class="toc-subsections">')
            for sub_number, subsection in enumerate(section.subsections, 1):
                toc.append(f'<li><a href="#{escape(subsection.slug or "subsection")}">{number}.{sub_number}. {escape(subsection.title)}</a></li>')
            toc.append("</ol>")
        toc.append("</li>")
        article.append(_section_html(section, number, environment_counters))

    related = []
    for link in document.related_links:
        related.append(f'<li><a href="{escape(link.href, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(link.name)}</a></li>')

    replacements = {
        "{{DOCUMENT_TITLE}}": "",
        "{{ARTICLE_TITLE}}": escape(document.article_title),
        "{{BANNER}}": banner,
        "{{BUTTONS}}": "\n".join(buttons),
        "{{TOC}}": "\n".join(toc),
        "{{ARTICLE}}": "\n".join(article),
        "{{RELATED_LINKS}}": "\n".join(related),
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    return template
