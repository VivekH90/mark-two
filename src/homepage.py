"""Homepage generation for Mark Two projects."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from .site_config import created_artifacts_root, find_project_root, load_config


DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "web" / "homepage.html"
DATE_FORMATS = (
    "%Y-%m-%d",
    "%d %B %Y",
    "%d %b %Y",
    "%B %d, %Y",
    "%b %d, %Y",
)
TOPIC_LIMIT = 5
RECENT_LIMIT = 5
ARCHIVE_LIMIT = 12


def _load_articles(root: Path) -> list[dict[str, Any]]:
    path = root / "articles.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"Mark Two article catalog not found: {path}. Compile at least one article first."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("articles", []), list):
        raise ValueError(f"Mark Two article catalog must contain an 'articles' array: {path}")
    return [article for article in data["articles"] if isinstance(article, dict)]


def _parse_date(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            pass
    return None


def _sort_key(article: dict[str, Any]) -> tuple[datetime, str]:
    return (
        _parse_date(article.get("date")) or datetime.min,
        str(article.get("title", "")).casefold(),
    )


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-") or "topic"


def _topic_class(subject: str) -> str:
    normalized = subject.strip().casefold()
    if normalized in {"physics", "physical physics"}:
        return "physics"
    if normalized in {"math", "mathematics"}:
        return "math"
    if normalized in {"notes", "thoughts"}:
        return "notes"
    return f"topic-{sum(map(ord, normalized)) % 3}"


def _long_display_date(value: Any) -> str:
    parsed = _parse_date(value)
    if parsed:
        return f"{parsed.day} {parsed:%B} {parsed:%Y}"
    return str(value or "Undated")


def _display_date(value: Any) -> tuple[str, str]:
    parsed = _parse_date(value)
    if parsed:
        return f"{parsed:%b} {parsed.day:02d}", f"{parsed:%Y}"
    text = str(value or "")
    return text, text[:4] if len(text) >= 4 and text[:4].isdigit() else ""


def _description(article: dict[str, Any]) -> str:
    return str(article.get("description") or article.get("summary") or "").strip()


def _article_url(article: dict[str, Any]) -> str:
    return str(article.get("url") or "#")


def _doctype(article: dict[str, Any]) -> str:
    value = str(article.get("doctype") or "notes").strip().casefold()
    return value if value in {"article", "notes"} else "article"


def _doctype_label(value: str) -> str:
    return "Notes" if value == "notes" else "Article"


def _email_url(value: Any) -> str:
    """Turn a configured email address into a mailto link."""
    email = str(value or "").strip()
    if not email:
        return "#"
    if email.casefold().startswith("mailto:"):
        return email
    return f"mailto:{email}"


def _render_featured(article: dict[str, Any] | None) -> str:
    if article is None:
        return '<p class="empty-msg" style="display:block">No featured article configured.</p>'
    subject = str(article.get("subject") or article.get("folder") or "Article")
    description = _description(article)
    description_html = f"<p>{escape(description)}</p>" if description else ""
    title = escape(str(article.get("title") or "Untitled"))
    url = escape(_article_url(article), quote=True)
    display_date, _ = _display_date(article.get("date"))
    return (
        f'<article class="featured-card {_topic_class(subject)}" data-doctype="{_doctype(article)}">'
        f'<span class="badge">{escape(subject)}</span>'
        f'<h3><a href="{url}">{title}</a></h3>'
        f'{description_html}'
        f'<div class="meta">{escape(display_date or "Undated")}</div>'
        f'</article>'
    )


def _render_recent(articles: list[dict[str, Any]]) -> str:
    cards = []
    for article in articles[:RECENT_LIMIT]:
        description = _description(article)
        title_text = str(article.get("title") or "Untitled")
        title = escape(title_text)
        url = escape(_article_url(article), quote=True)
        tags = article.get("tags", [])
        tags = tags if isinstance(tags, list) else []
        tag_slugs = [_slug(str(tag)) for tag in tags if str(tag).strip()]
        tag_data = "|".join(escape(slug, quote=True) for slug in tag_slugs)
        search_fields = [title_text, description, *[str(tag) for tag in tags]]
        search = escape(" ".join(search_fields), quote=True)
        tag_html = "".join(
            f'<span class="chip" data-topic="{escape(_slug(str(tag)), quote=True)}">{escape(str(tag))}</span>'
            for tag in tags if str(tag).strip()
        )
        description_html = f"<p>{escape(description)}</p>" if description else ""
        cards.append(
            f'<article class="recent-card" data-doctype="{_doctype(article)}" data-tags="{tag_data}" data-search="{search}">'
            f'<time class="date">{escape(_long_display_date(article.get("date")))}</time>'
            f'<div class="recent-body">'
            f'<h3><a href="{url}">{title}</a></h3>'
            f'{description_html}'
            f'<div class="recent-type">{escape(_doctype_label(_doctype(article)))}</div>'
            f'<div class="recent-tags">{tag_html}</div>'
            f'</div>'
            f'</article>'
        )
    return "\n".join(cards) or '<p class="recent-empty" style="display:block">No articles found.</p>'

def _render_topics(articles: list[dict[str, Any]]) -> str:
    counts: Counter[str] = Counter()
    labels: dict[str, str] = {}
    for article in articles:
        tags = article.get("tags", [])
        if not isinstance(tags, list):
            continue
        for raw in tags:
            tag = str(raw).strip()
            if tag:
                key = tag.casefold()
                counts[key] += 1
                labels.setdefault(key, tag)

    ordered = sorted(counts, key=lambda key: (-counts[key], labels[key].casefold()))
    return "\n".join(
        f'<button type="button" class="chip" data-topic="{escape(_slug(labels[key]), quote=True)}">'
        f'{escape(labels[key])}<small>{counts[key]}</small></button>'
        for key in ordered[:TOPIC_LIMIT]
    ) or '<span class="filter-note">No tags yet.</span>'


def _render_archive(articles: list[dict[str, Any]]) -> str:
    grouped: dict[str, list[str]] = defaultdict(list)
    for article in articles[:ARCHIVE_LIMIT]:
        display_date, year = _display_date(article.get("date"))
        year = year or "Other"
        subject = str(article.get("subject") or article.get("folder") or "Article")
        tags = article.get("tags", [])
        tag_slugs = [_slug(str(tag)) for tag in tags] if isinstance(tags, list) else []
        search_fields = [
            article.get("title", ""),
            _description(article),
            subject,
            article.get("folder", ""),
            " ".join(str(tag) for tag in tags),
        ]
        search = escape(" ".join(str(x) for x in search_fields), quote=True)
        tag_data = "|".join(escape(tag, quote=True) for tag in tag_slugs)
        grouped[year].append(
            f'<div class="row {_topic_class(subject)}" data-doctype="{_doctype(article)}" data-tags="{tag_data}" data-search="{search}">'
            f'<time>{escape(display_date)}</time>'
            f'<a class="ttl" href="{escape(_article_url(article), quote=True)}">{escape(str(article.get("title") or "Untitled"))}</a>'
            f'<span class="cat">{escape(subject)}</span>'
            f'</div>'
        )

    chunks = []
    for year in sorted(grouped, reverse=True):
        chunks.append(f'<div class="year-label" data-year="{escape(year, quote=True)}">{escape(year)}</div>')
        chunks.extend(grouped[year])
    return "\n".join(chunks)


def build_homepage(
    root: str | Path = ".",
    output: str | Path | None = None,
    template: str | Path | None = None,
) -> Path:
    root = find_project_root(root)
    config = load_config(root)
    articles = sorted(_load_articles(root), key=_sort_key, reverse=True)
    template_path = Path(template).resolve() if template else DEFAULT_TEMPLATE.resolve()
    output_path = Path(output).resolve() if output else created_artifacts_root(root) / "index.html"

    if not template_path.is_file():
        raise FileNotFoundError(f"Homepage template not found: {template_path}")

    featured_id = str(config.get("featured") or "")
    featured = next(
        (
            article for article in articles
            if str(article.get("id", "")) == featured_id
            or str(article.get("source", "")) == featured_id
            or str(article.get("url", "")) == featured_id
        ),
        None,
    )

    author = str(config.get("author") or "Author")
    avatar = "".join(part[0] for part in author.split()[:2]).upper() or "MT"
    replacements = {
        "SITE_TITLE": escape(str(config.get("title") or "Notes")),
        "AUTHOR": escape(author),
        "BIO": escape(str(config.get("bio") or "")),
        "AVATAR": escape(avatar),
        "GITHUB_URL": escape(str(config.get("github") or "#"), quote=True),
        "EMAIL_URL": escape(_email_url(config.get("email")), quote=True),
        "INSTAGRAM_URL": escape(str(config.get("instagram") or "#"), quote=True),
        "ABOUT_URL": escape(str(config.get("about") or "#"), quote=True),
        "ARCHIVE_URL": escape(str(config.get("archive") or "#"), quote=True),
        "YEAR": escape(str(config.get("copyright") or datetime.now().year)),
        "SITE_DESCRIPTION": escape(str(config.get("description") or "")),
        "FEATURED": _render_featured(featured),
        "RECENT": _render_recent(articles),
        "TOPICS": _render_topics(articles),
        "ARCHIVE": _render_archive(articles),
    }

    html = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        html = html.replace("{{" + key + "}}", value)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
