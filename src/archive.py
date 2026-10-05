"""Archive page generation for Mark Two projects."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from .homepage import (
    _article_url,
    _description,
    _display_date,
    _load_articles,
    _parse_date,
    _slug,
    _sort_key,
)
from .site_config import find_project_root, load_config


DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "web" / "archive.html"


def _month_label(value: Any) -> tuple[datetime | None, str]:
    parsed = _parse_date(value)
    if parsed:
        return parsed, f"{parsed:%B} {parsed:%Y}"
    return None, "Other"


def _render_tag_filter(articles: list[dict[str, Any]]) -> str:
    counts: Counter[str] = Counter()
    labels: dict[str, str] = {}

    for article in articles:
        tags = article.get("tags", [])
        if not isinstance(tags, list):
            continue
        for raw in tags:
            tag = str(raw).strip()
            if not tag:
                continue
            key = _slug(tag)
            counts[key] += 1
            labels.setdefault(key, tag)

    ordered = sorted(
        counts,
        key=lambda key: (-counts[key], labels[key].casefold()),
    )
    return "".join(
        f'<button type="button" class="chip" data-tag="{escape(key, quote=True)}">'
        f'{escape(labels[key])}<small>{counts[key]}</small></button>'
        for key in ordered
    ) or '<span class="filter-note">No tags yet.</span>'


def _render_rows(articles: list[dict[str, Any]]) -> str:
    groups: dict[str, list[str]] = defaultdict(list)
    group_order: list[tuple[datetime | None, str]] = []

    for article in articles:
        parsed, month = _month_label(article.get("date"))
        tags = article.get("tags", [])
        tags = tags if isinstance(tags, list) else []
        clean_tags = [str(tag).strip() for tag in tags if str(tag).strip()]
        tag_slugs = [_slug(tag) for tag in clean_tags]
        tag_data = "|".join(escape(slug, quote=True) for slug in tag_slugs)

        title_text = str(article.get("title") or "Untitled")
        description = _description(article)
        subject = str(article.get("subject") or article.get("folder") or "Article")
        search_fields = [
            title_text,
            description,
            subject,
            str(article.get("folder") or ""),
            " ".join(clean_tags),
        ]
        search = escape(" ".join(search_fields), quote=True)

        tag_html = "".join(
            f'<span class="chip" data-tag="{escape(_slug(tag), quote=True)}">{escape(tag)}</span>'
            for tag in clean_tags
        )

        display_date, _ = _display_date(article.get("date"))
        description_html = (
            f'<p class="archive-description">{escape(description)}</p>'
            if description else ""
        )
        row = (
            f'<article class="archive-row" data-tags="{tag_data}" data-search="{search}">'
            f'<time class="archive-date">{escape(display_date or "Undated")}</time>'
            f'<div class="archive-body">'
            f'<a class="archive-title" href="{escape(_article_url(article), quote=True)}">{escape(title_text)}</a>'
            f'{description_html}'
            f'<div class="archive-tags">{tag_html}</div>'
            f'</div>'
            f'</article>'
        )
        key = month
        if key not in groups:
            groups[key] = []
            group_order.append((parsed, key))
        groups[key].append(row)

    group_order.sort(key=lambda item: item[0] or datetime.min, reverse=True)

    out: list[str] = []
    for _, month in group_order:
        out.append(f'<h2 class="month" data-month="{escape(month, quote=True)}">{escape(month)}</h2>')
        out.extend(groups[month])

    return "
".join(out) or '<p class="empty" style="display:block">No articles found.</p>'


def build_archive(
    root: str | Path = ".",
    output: str | Path | None = None,
    template: str | Path | None = None,
) -> Path:
    root = find_project_root(root)
    config = load_config(root)
    articles = sorted(_load_articles(root), key=_sort_key, reverse=True)
    template_path = Path(template).resolve() if template else DEFAULT_TEMPLATE.resolve()
    output_path = Path(output).resolve() if output else root / "archive" / "index.html"

    replacements = {
        "SITE_TITLE": escape(str(config.get("title") or "Notes")),
        "AUTHOR": escape(str(config.get("author") or "Author")),
        "GITHUB_URL": escape(str(config.get("github") or "#"), quote=True),
        "ABOUT_URL": escape(str(config.get("about") or "#"), quote=True),
        "HOME_URL": escape("/"),
        "ARCHIVE_URL": escape(str(config.get("archive") or "/archive/"), quote=True),
        "YEAR": escape(str(config.get("copyright") or datetime.now().year)),
        "TAG_FILTER": _render_tag_filter(articles),
        "ARCHIVE_ROWS": _render_rows(articles),
    }

    html = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        html = html.replace("{{" + key + "}}", value)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
