"""Remote image gallery providers for Mark Two."""

from __future__ import annotations

import json
import random
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .ast import GalleryItem, GallerySpec

_NASA_SEARCH = "https://images-api.nasa.gov/search"
_NASA_ASSET = "https://images-api.nasa.gov/asset/{nasa_id}"
_USER_AGENT = "Mark-Two/0.1"


def _get_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": _USER_AGENT})
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def _image_asset_url(nasa_id: str) -> str:
    manifest = _get_json(_NASA_ASSET.format(nasa_id=quote(nasa_id, safe="")))
    for item in manifest.get("collection", {}).get("items", []):
        href = item.get("href", "")
        if not href:
            continue
        lower = href.lower()
        if lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
            return href
    for item in manifest.get("collection", {}).get("items", []):
        href = item.get("href", "")
        if href and not href.lower().endswith((".txt", ".json", ".srt", ".vtt")):
            return href
    return ""


def fetch_nasa_gallery(spec: GallerySpec) -> list[GalleryItem]:
    """Search NASA's public image API and return remote image URLs plus credits."""
    params = urlencode({
        "q": spec.query,
        "media_type": "image",
        "page_size": min(max(spec.count * 4, 20), 100),
    })
    data = _get_json(f"{_NASA_SEARCH}?{params}")
    candidates = []

    for item in data.get("collection", {}).get("items", []):
        data_block = item.get("data", [{}])[0]
        nasa_id = data_block.get("nasa_id", "")
        if not nasa_id:
            continue
        candidates.append((
            nasa_id,
            data_block.get("title", ""),
            data_block.get("description", ""),
            data_block.get("center", "NASA"),
            f"https://images.nasa.gov/details/{quote(nasa_id, safe='')}",
        ))

    if not candidates:
        raise RuntimeError(f'NASA returned no images for query "{spec.query}".')

    rng = random.Random(spec.seed)
    rng.shuffle(candidates)

    gallery = []
    seen_urls = set()
    for nasa_id, title, description, credit, source_url in candidates:
        try:
            url = _image_asset_url(nasa_id)
        except Exception:
            continue
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        gallery.append(GalleryItem(
            url=url,
            title=title,
            alt=description or title or "NASA image",
            source_url=source_url,
            credit=credit or "NASA",
        ))
        if len(gallery) >= spec.count:
            break

    if not gallery:
        raise RuntimeError(f'NASA images were found, but no usable image assets could be resolved for "{spec.query}".')
    return gallery


def resolve_gallery(spec: GallerySpec) -> list[GalleryItem]:
    """Resolve a gallery provider into remote image metadata."""
    if spec.source.lower() == "nasa":
        return fetch_nasa_gallery(spec)
    raise ValueError(f"Unsupported gallery source: {spec.source}")
