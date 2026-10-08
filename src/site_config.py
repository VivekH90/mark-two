"""Site configuration helpers for Mark Two."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


CONFIG_FILENAME = "site.json"
CREATED_ARTIFACTS_DIRNAME = "created artifacts"


def created_artifacts_root(root: str | Path) -> Path:
    """Return the directory containing generated HTML artifacts."""
    return Path(root).resolve() / CREATED_ARTIFACTS_DIRNAME

DEFAULT_CONFIG = {
    "author": "",
    "bio": "",
    "title": "Notes on mathematics & physics",
    "description": "",
    "email": "",
    "instagram": "",
    "github": "",
    "about": "/about/",
    "archive": "/archive/",
    "featured": "",
    "copyright": str(datetime.now().year),
}


def find_project_root(start: str | Path = ".") -> Path:
    """Find the nearest directory that looks like a Mark Two project root."""
    path = Path(start).resolve()
    if path.is_file():
        path = path.parent

    for candidate in (path, *path.parents):
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").is_file():
            return candidate
    return path


def config_path(root: str | Path) -> Path:
    return Path(root).resolve() / CONFIG_FILENAME


def load_config(root: str | Path) -> dict[str, Any]:
    """Load site.json, filling missing optional values from the defaults."""
    path = config_path(root)
    if not path.is_file():
        raise FileNotFoundError(
            f"Mark Two site configuration not found: {path}. Run 'mark-two init' first."
        )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Mark Two site configuration must be a JSON object: {path}")

    merged = dict(DEFAULT_CONFIG)
    merged.update(data)
    return merged


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp:
            temp.write(payload)
            temp.flush()
            os.fsync(temp.fileno())
            temp_path = Path(temp.name)
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def init_site(root: str | Path, force: bool = False) -> Path:
    """Create a site.json configuration file."""
    path = config_path(root)
    if path.exists() and not force:
        raise FileExistsError(
            f"{path} already exists. Use 'mark-two init --force' to replace it."
        )
    _write_json(path, dict(DEFAULT_CONFIG))
    return path


def set_config(root: str | Path, key: str, value: str) -> Path:
    """Set one supported top-level site configuration field."""
    allowed = set(DEFAULT_CONFIG)
    if key not in allowed:
        valid = ", ".join(sorted(allowed))
        raise KeyError(f"Unknown config key '{key}'. Valid keys: {valid}")

    path = config_path(root)
    data = load_config(root)
    data[key] = value
    _write_json(path, data)
    return path


def get_config(root: str | Path, key: str | None = None) -> Any:
    """Read one config value, or the whole configuration when key is omitted."""
    data = load_config(root)
    if key is None:
        return data
    if key not in data:
        valid = ", ".join(sorted(data))
        raise KeyError(f"Unknown config key '{key}'. Valid keys: {valid}")
    return data[key]
