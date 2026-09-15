"""Render a Mark Two Document into the article HTML template."""

from html import escape
from pathlib import Path

from .ast import Document, Section, Subsection


def _paragraphs(lines):
    if not lines:
        return ""
    paragraphs = []
    current = []
    for line in lines:
        if line:
            current.append(line)
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    return "\n".join(f'<p>{escape(p)}</p>' for p in paragraphs)


def _section_html(section: Section, number: int) -> str:
    html = [f'<section class="article-section" id="{escape(section.slug or "section")}">']
    html.append(f'<h2>{number}. {escape(section.title)}</h2>')
    html.append(_paragraphs(section.content))

    for sub_number, subsection in enumerate(section.subsections, 1):
        html.append(
            f'<section class="article-subsection" id="{escape(subsection.slug or "subsection")}">'
        )
        html.append(
            f'<h3>{number}.{sub_number}. {escape(subsection.title)}</h3>'
        )
        html.append(_paragraphs(subsection.content))
        html.append('</section>')

    html.append('</section>')
    return "\n".join(html)


def render(document: Document, template_path: str | Path) -> str:
    template = Path(template_path).read_text(encoding="utf-8")

    buttons = []
    for button in document.buttons:
        color = escape(button.color, quote=True)
        buttons.append(
            f'<a class="nav-button" href="{escape(button.href, quote=True)}" '
            f'data-color="{color}">{escape(button.name)}</a>'
        )

    toc = []
    article = []
    for number, section in enumerate(document.sections, 1):
        toc.append(
            f'<li><a href="#{escape(section.slug or "section")}">'
            f'{number}. {escape(section.title)}</a>'
        )
        if section.subsections:
            toc.append('<ol class="toc-subsections">')
            for sub_number, subsection in enumerate(section.subsections, 1):
                toc.append(
                    f'<li><a href="#{escape(subsection.slug or "subsection")}">'
                    f'{number}.{sub_number}. {escape(subsection.title)}</a></li>'
                )
            toc.append('</ol>')
        toc.append('</li>')
        article.append(_section_html(section, number))

    related = []
    for link in document.related_links:
        related.append(
            f'<li><a href="{escape(link.href, quote=True)}" target="_blank" '
            f'rel="noopener noreferrer">{escape(link.name)}</a></li>'
        )

    replacements = {
        "{{DOCUMENT_TITLE}}": escape(document.document_title),
        "{{ARTICLE_TITLE}}": escape(document.article_title),
        "{{BUTTONS}}": "\n".join(buttons),
        "{{TOC}}": "\n".join(toc),
        "{{ARTICLE}}": "\n".join(article),
        "{{RELATED_LINKS}}": "\n".join(related),
    }

    for key, value in replacements.items():
        template = template.replace(key, value)
    return template
