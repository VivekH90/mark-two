"""Helpers for producing self-contained HTML bundles."""

from __future__ import annotations

import re
from pathlib import Path


_STYLE_LINK = re.compile(
    r'<link(?=[^>]*\brel\s*=\s*["\']stylesheet["\'])(?=[^>]*\bhref\s*=\s*["\'](?:\./)?style\.css["\'])[^>]*>\s*',
    re.IGNORECASE,
)

_SCRIPT_TAG = re.compile(
    r'<script(?=[^>]*\bsrc\s*=\s*["\'](?:\./)?script\.js["\'])[^>]*>\s*</script>\s*',
    re.IGNORECASE,
)


def inline_web_assets(html: str, asset_directory: str | Path) -> str:
    """Inline Mark Two's local stylesheet and JavaScript into the HTML.

    Only the template's local style.css and script.js are inlined.
    External assets, such as the MathJax CDN script, are left untouched.
    """
    asset_directory = Path(asset_directory).resolve()

    style_path = asset_directory / "style.css"
    script_path = asset_directory / "script.js"

    if not style_path.is_file():
        raise FileNotFoundError(f"Required template asset not found: {style_path}")
    if not script_path.is_file():
        raise FileNotFoundError(f"Required template asset not found: {script_path}")

    style = style_path.read_text(encoding="utf-8")
    script = script_path.read_text(encoding="utf-8")

    html, style_count = _STYLE_LINK.subn(
        lambda _: f"<style>\n{style}\n</style>\n",
        html,
        count=1,
    )
    html, script_count = _SCRIPT_TAG.subn(
        lambda _: f"<script>\n{script}\n</script>\n",
        html,
        count=1,
    )

    if style_count == 0:
        raise ValueError("Mark Two template does not contain its local style.css link.")
    if script_count == 0:
        raise ValueError("Mark Two template does not contain its local script.js tag.")

    return html
