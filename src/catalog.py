"""Generated article metadata catalog for Mark Two projects."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .ast import DOCUMENT_TYPES, Document


INDEX_VERSION = 2
INDEX_FILENAME = "articles.json"


def _find_project_root(source_path: Path) -> Path:
    """Find the nearest project root from a Mark Two source file.

    A directory containing either .git or pyproject.toml is treated as a
    project root. If no root marker exists, the current working directory is
    used so an explicit command such as `mark-two /path/to/article.mt`
    still has a predictable catalog location.
    """
    source_path = source_path.resolve()
    for candidate in (source_path.parent, *source_path.parents):
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").is_file():
            return candidate
    return Path.cwd().resolve()


def resolve_catalog_path(
    source_path: str | Path,
    index_path: str | Path | None = None,
) -> Path:
    """Resolve the catalog path used for one compilation."""
    if index_path is not None:
        return Path(index_path).resolve()
    return _find_project_root(Path(source_path)) / INDEX_FILENAME


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(
            f"Path '{path}' is outside the catalog project root '{root}'. "
            "Use --index to place the catalog in a project containing the article."
        ) from exc


def _article_id(source_path: Path, root: Path) -> str:
    relative = Path(_relative_path(source_path, root))
    return relative.with_suffix("").as_posix()


def _article_url(output_path: Path, root: Path) -> str:
    relative = _relative_path(output_path, root)
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        directory = relative[: -len("index.html")]
        return f"/{directory}"
    return f"/{relative}"


def _normalise_tags(tags: list[str]) -> list[str]:
    """Trim tags and remove duplicates without changing their first spelling."""
    result: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        cleaned = tag.strip()
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def build_catalog_entry(
    document: Document,
    source_path: str | Path,
    output_path: str | Path,
    root: str | Path,
) -> dict[str, object]:
    """Build the JSON record representing one compiled article."""
    source = Path(source_path).resolve()
    output = Path(output_path).resolve()
    project_root = Path(root).resolve()

    relative_source = _relative_path(source, project_root)
    doctype = str(document.doctype or "").strip().casefold()
    if doctype not in DOCUMENT_TYPES:
        allowed = " or ".join(DOCUMENT_TYPES)
        raise ValueError(f"Document type must be {allowed}")

    return {
        "id": _article_id(source, project_root),
        "doctype": doctype,
        "title": document.article_title,
        "description": document.description,
        "subject": document.document_tag,
        "folder": document.folder,
        "author": document.author,
        "date": document.date,
        "tags": _normalise_tags(document.tags),
        "url": _article_url(output, project_root),
        "source": relative_source,
        "sections": [section.title for section in document.sections],
    }


def _load_catalog(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"version": INDEX_VERSION, "articles": []}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Could not read Mark Two catalog '{path}': invalid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(f"Mark Two catalog '{path}' must contain a JSON object.")

    articles = data.get("articles")
    if articles is None:
        data["articles"] = []
    elif not isinstance(articles, list):
        raise ValueError(
            f"Mark Two catalog '{path}' must store articles as a JSON array."
        )

    data["version"] = INDEX_VERSION
    return data


def _write_catalog(path: Path, data: dict[str, object]) -> None:
    """Write the catalog atomically so an interrupted compile cannot corrupt it."""
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
    ) + "\n"

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(payload)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def update_catalog(
    document: Document,
    source_path: str | Path,
    output_path: str | Path,
    index_path: str | Path | None = None,
) -> Path:
    """Create or update exactly one article record in the generated catalog.

    Existing articles keep their position and contents. A new article is
    appended. The JSON file is rewritten atomically because JSON is a single
    text document, but only the matching article record is logically changed.
    """
    source = Path(source_path).resolve()
    output = Path(output_path).resolve()
    catalog_path = resolve_catalog_path(source, index_path)

    project_root = catalog_path.parent.resolve()
    entry = build_catalog_entry(document, source, output, project_root)
    data = _load_catalog(catalog_path)
    articles = data["articles"]

    if not isinstance(articles, list):
        raise ValueError(f"Mark Two catalog '{catalog_path}' has invalid articles data.")

    matching_indexes = [
        index
        for index, article in enumerate(articles)
        if isinstance(article, dict) and article.get("id") == entry["id"]
    ]

    if matching_indexes:
        first = matching_indexes[0]
        if len(matching_indexes) == 1 and articles[first] == entry:
            return catalog_path
        articles[first] = entry
        for index in reversed(matching_indexes[1:]):
            del articles[index]
    else:
        articles.append(entry)

    _write_catalog(catalog_path, data)
    return catalog_path
