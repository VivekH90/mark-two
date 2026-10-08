"""About page generation for Mark Two projects."""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

from .site_config import created_artifacts_root, find_project_root, load_config, relative_site_url

DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "web" / "about.html"


def build_about(root=".", output=None, template=None) -> Path:
    root = find_project_root(root)
    config = load_config(root)
    template_path = Path(template).resolve() if template else DEFAULT_TEMPLATE.resolve()
    output_path = Path(output).resolve() if output else created_artifacts_root(root) / "about" / "index.html"

    replacements = {
        "SITE_TITLE": escape(str(config.get("title") or "Notes")),
        "AUTHOR": escape(str(config.get("author") or "Author")),
        "BIO": escape(str(config.get("bio") or "")),
        "GITHUB_URL": escape(str(config.get("github") or "#"), quote=True),
        "HOME_URL": escape(relative_site_url(root, output_path, "/"), quote=True),
        "ARCHIVE_URL": escape(relative_site_url(root, output_path, str(config.get("archive") or "/archive/")), quote=True),
        "ABOUT_URL": escape(relative_site_url(root, output_path, str(config.get("about") or "/about/")), quote=True),
        "YEAR": escape(str(config.get("copyright") or datetime.now().year)),
    }

    html = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        html = html.replace("{{" + key + "}}", value)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
