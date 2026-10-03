"""Remote image gallery providers for Mark Two."""

from __future__ import annotations

import html
import json
import random
import re
from ast import literal_eval
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .ast import GalleryItem, GallerySpec

_NASA_SEARCH = "https://images-api.nasa.gov/search"
_NASA_ASSET = "https://images-api.nasa.gov/asset/{nasa_id}"

_OPENVERSE_SEARCH = "https://api.openverse.org/v1/images/"

_WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"

_MET_SEARCH = "https://collectionapi.metmuseum.org/public/collection/v1.1/search"
_MET_OBJECT = "https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}"

_INTERNET_ARCHIVE_SEARCH = "https://archive.org/advancedsearch.php"
_INTERNET_ARCHIVE_IMAGE = "https://archive.org/services/img/{identifier}"

_ESA_HUBBLE_JSON = "https://esahubble.org/images/json/"

_USER_AGENT = "Mark-Two/0.1"


def _get_json(url: str):
    request = Request(
        url,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def _get_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": _USER_AGENT})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", "replace")


def _clean_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace").strip()
    if isinstance(value, dict):
        if "value" in value:
            value = value["value"]
        elif "url" in value:
            value = value["url"]
        else:
            value = next(iter(value.values()), "")
    value = str(value).strip()

    # Some providers include HTML in descriptive metadata.
    value = html.unescape(re.sub(r"<[^>]+>", "", value))
    return " ".join(value.split())


def _join_credit(*parts: str) -> str:
    values = []
    for part in parts:
        cleaned = _clean_text(part)
        if cleaned and cleaned not in values:
            values.append(cleaned)
    return " · ".join(values)


def _shuffle_candidates(candidates, spec: GallerySpec):
    rng = random.Random(spec.seed)
    rng.shuffle(candidates)
    return candidates


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

    candidates = _shuffle_candidates(candidates, spec)

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
        raise RuntimeError(
            f'NASA images were found, but no usable image assets could be resolved for "{spec.query}".'
        )
    return gallery


def fetch_openverse_gallery(spec: GallerySpec) -> list[GalleryItem]:
    """Search Openverse for openly licensed images."""
    params = urlencode({
        "q": spec.query,
        "page_size": min(max(spec.count * 4, 20), 100),
    })
    data = _get_json(f"{_OPENVERSE_SEARCH}?{params}")

    candidates = []
    for item in data.get("results", []):
        url = item.get("url", "")
        if not url:
            continue
        source_url = (
            item.get("foreign_landing_url")
            or item.get("detail_url")
            or item.get("url")
        )
        title = _clean_text(item.get("title", ""))
        creator = _clean_text(item.get("creator", ""))
        provider = _clean_text(item.get("provider", "Openverse"))
        license_name = _clean_text(item.get("license", ""))
        credit = _join_credit(creator, provider, license_name)

        candidates.append((
            url,
            title,
            _clean_text(item.get("description", "")),
            source_url,
            credit,
        ))

    if not candidates:
        raise RuntimeError(f'Openverse returned no images for query "{spec.query}".')

    candidates = _shuffle_candidates(candidates, spec)
    gallery = []
    seen_urls = set()
    for url, title, description, source_url, credit in candidates:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        gallery.append(GalleryItem(
            url=url,
            title=title,
            alt=description or title or "Openverse image",
            source_url=source_url,
            credit=credit or "Openverse",
        ))
        if len(gallery) >= spec.count:
            break

    return gallery


def _wikimedia_metadata_value(metadata: dict, key: str) -> str:
    return _clean_text(metadata.get(key, ""))


def fetch_wikimedia_gallery(spec: GallerySpec) -> list[GalleryItem]:
    """Search Wikimedia Commons files through the public MediaWiki API."""
    params = urlencode({
        "action": "query",
        "generator": "search",
        "gsrsearch": spec.query,
        "gsrnamespace": 6,
        "gsrlimit": min(max(spec.count * 4, 20), 50),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": 1200,
        "format": "json",
        "formatversion": 2,
    })
    data = _get_json(f"{_WIKIMEDIA_API}?{params}")

    candidates = []
    for page in data.get("query", {}).get("pages", []):
        title = page.get("title", "")
        imageinfo = (page.get("imageinfo") or [{}])[0]
        url = imageinfo.get("thumburl") or imageinfo.get("url", "")
        if not url:
            continue

        metadata = imageinfo.get("extmetadata", {})
        description = _wikimedia_metadata_value(metadata, "ImageDescription")
        artist = _wikimedia_metadata_value(metadata, "Artist")
        credit = _wikimedia_metadata_value(metadata, "Credit")
        license_name = _wikimedia_metadata_value(metadata, "LicenseShortName")
        composed_credit = _join_credit(artist or credit, license_name, "Wikimedia Commons")

        file_title = quote(title.removeprefix("File:"), safe="")
        source_url = f"https://commons.wikimedia.org/wiki/File:{file_title}"

        candidates.append((
            url,
            _clean_text(title.removeprefix("File:")),
            description,
            source_url,
            composed_credit,
        ))

    if not candidates:
        raise RuntimeError(f'Wikimedia Commons returned no images for query "{spec.query}".')

    candidates = _shuffle_candidates(candidates, spec)
    gallery = []
    seen_urls = set()
    for url, title, description, source_url, credit in candidates:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        gallery.append(GalleryItem(
            url=url,
            title=title,
            alt=description or title or "Wikimedia Commons image",
            source_url=source_url,
            credit=credit or "Wikimedia Commons",
        ))
        if len(gallery) >= spec.count:
            break

    return gallery


def fetch_met_gallery(spec: GallerySpec) -> list[GalleryItem]:
    """Search The Met's Open Access collection for public-domain images."""
    params = urlencode({
        "q": spec.query,
        "hasImages": "true",
        "limit": min(max(spec.count * 4, 20), 500),
    })
    data = _get_json(f"{_MET_SEARCH}?{params}")

    object_ids = data.get("objectIDs", [])
    object_ids = _shuffle_candidates(object_ids[:], spec)

    gallery = []
    seen_urls = set()
    for object_id in object_ids:
        try:
            item = _get_json(_MET_OBJECT.format(object_id=quote(str(object_id), safe="")))
        except Exception:
            continue

        url = item.get("primaryImage", "")
        if not url or not item.get("isPublicDomain", False):
            continue
        if url in seen_urls:
            continue

        seen_urls.add(url)
        title = _clean_text(item.get("title", ""))
        artist = _clean_text(item.get("artistDisplayName", ""))
        department = _clean_text(item.get("department", "The Met"))
        source_url = f"https://www.metmuseum.org/art/collection/search/{quote(str(object_id), safe="")}"

        gallery.append(GalleryItem(
            url=url,
            title=title,
            alt=title or "Met Museum image",
            source_url=source_url,
            credit=_join_credit(artist, department, "The Metropolitan Museum of Art", "Public Domain"),
        ))
        if len(gallery) >= spec.count:
            break

    if not gallery:
        raise RuntimeError(
            f'The Met returned no usable public-domain images for query "{spec.query}".'
        )
    return gallery


def fetch_internet_archive_gallery(spec: GallerySpec) -> list[GalleryItem]:
    """Search Internet Archive image items through its public Advanced Search API."""
    params = [
        ("q", f"{spec.query} AND mediatype:image"),
        ("fl[]", "identifier"),
        ("fl[]", "title"),
        ("fl[]", "description"),
        ("fl[]", "creator"),
        ("rows", min(max(spec.count * 4, 20), 100)),
        ("output", "json"),
    ]
    data = _get_json(f"{_INTERNET_ARCHIVE_SEARCH}?{urlencode(params)}")

    docs = data.get("response", {}).get("docs", [])
    docs = _shuffle_candidates(docs, spec)

    gallery = []
    seen_urls = set()
    for item in docs:
        identifier = item.get("identifier", "")
        if not identifier:
            continue

        url = _INTERNET_ARCHIVE_IMAGE.format(
            identifier=quote(identifier, safe="")
        )
        if url in seen_urls:
            continue

        seen_urls.add(url)
        title = _clean_text(item.get("title", ""))
        description = _clean_text(item.get("description", ""))
        creator = _clean_text(item.get("creator", ""))
        source_url = f"https://archive.org/details/{quote(identifier, safe='')}"

        gallery.append(GalleryItem(
            url=url,
            title=title,
            alt=description or title or "Internet Archive image",
            source_url=source_url,
            credit=_join_credit(creator, "Internet Archive"),
        ))
        if len(gallery) >= spec.count:
            break

    if not gallery:
        raise RuntimeError(
            f'Internet Archive returned no image items for query "{spec.query}".'
        )
    return gallery


def _esa_value(record: dict, *keys: str) -> str:
    for key in keys:
        if key in record:
            value = record[key]
            if isinstance(value, str) and value.startswith("b'") and value.endswith("'"):
                try:
                    parsed = literal_eval(value)
                    if isinstance(parsed, bytes):
                        return parsed.decode("utf-8", "replace").strip()
                except (ValueError, SyntaxError):
                    pass
            return _clean_text(value)
    return ""


def _esa_image_url(record: dict) -> str:
    for key in (
        "ImageURL",
        "image_url",
        "OriginalURL",
        "original_url",
        "OriginalImage",
        "original_image",
        "ThumbnailURL",
        "thumbnail_url",
        "URL",
        "url",
    ):
        value = _esa_value(record, key)
        if value.startswith("http://") or value.startswith("https://"):
            if any(ext in value.lower() for ext in (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")):
                return value
    return ""


def _esa_og_image(url: str) -> str:
    try:
        page = _get_text(url)
    except Exception:
        return ""

    match = re.search(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        page,
        re.IGNORECASE,
    )
    if match:
        return html.unescape(match.group(1))

    match = re.search(
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        page,
        re.IGNORECASE,
    )
    return html.unescape(match.group(1)) if match else ""


def _esa_records(data):
    if isinstance(data, list):
        return data
    for key in ("results", "images", "items", "objects", "data"):
        value = data.get(key) if isinstance(data, dict) else None
        if isinstance(value, list):
            return value
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return value
    return []


def fetch_esa_hubble_gallery(spec: GallerySpec) -> list[GalleryItem]:
    """Search the public ESA/Hubble image feed without authentication."""
    data = _get_json(_ESA_HUBBLE_JSON)
    records = _esa_records(data)

    query_terms = [term.lower() for term in re.findall(r"[\w]+", spec.query)]
    candidates = []

    for record in records:
        if not isinstance(record, dict):
            continue

        title = _esa_value(record, "Title", "title")
        description = _esa_value(record, "Description", "description")
        creator = _esa_value(record, "Creator", "creator")
        credit = _esa_value(record, "Credit", "credit")
        rights = _esa_value(record, "Rights", "rights")
        reference_url = _esa_value(record, "ReferenceURL", "reference_url", "ReferenceUrl")
        identifier = _esa_value(record, "ID", "id")

        haystack = " ".join(
            value.lower()
            for value in (title, description, creator, credit)
            if value
        )
        if query_terms and not all(term in haystack for term in query_terms):
            continue

        image_url = _esa_image_url(record)
        if not image_url and reference_url:
            image_url = _esa_og_image(reference_url)
        if not image_url:
            continue

        source_url = reference_url or (
            f"https://esahubble.org/images/{quote(identifier, safe='')}/"
            if identifier else image_url
        )

        candidates.append((
            image_url,
            title,
            description,
            source_url,
            _join_credit(credit or creator, rights, "ESA/Hubble"),
        ))

    if not candidates:
        raise RuntimeError(
            f'ESA/Hubble returned no usable images for query "{spec.query}". '
            "Its public feed currently exposes a finite result window, so very specific queries may miss it."
        )

    candidates = _shuffle_candidates(candidates, spec)
    gallery = []
    seen_urls = set()
    for url, title, description, source_url, credit in candidates:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        gallery.append(GalleryItem(
            url=url,
            title=title,
            alt=description or title or "ESA/Hubble image",
            source_url=source_url,
            credit=credit or "ESA/Hubble",
        ))
        if len(gallery) >= spec.count:
            break

    return gallery


_GALLERY_PROVIDERS = {
    "nasa": fetch_nasa_gallery,
    "openverse": fetch_openverse_gallery,
    "wikimedia": fetch_wikimedia_gallery,
    "wikimedia commons": fetch_wikimedia_gallery,
    "met": fetch_met_gallery,
    "the met": fetch_met_gallery,
    "internetarchive": fetch_internet_archive_gallery,
    "internet archive": fetch_internet_archive_gallery,
    "esa": fetch_esa_hubble_gallery,
    "esa/hubble": fetch_esa_hubble_gallery,
    "esahubble": fetch_esa_hubble_gallery,
    "esa hubble": fetch_esa_hubble_gallery,
}


def resolve_gallery(spec: GallerySpec) -> list[GalleryItem]:
    """Resolve a gallery provider into remote image metadata."""
    source = spec.source.strip().lower()
    provider = _GALLERY_PROVIDERS.get(source)
    if provider is None:
        available = ", ".join(sorted({
            "NASA",
            "Openverse",
            "Wikimedia",
            "Met",
            "Internet Archive",
            "ESA/Hubble",
        }))
        raise ValueError(
            f"Unsupported gallery source: {spec.source}. "
            f"Supported sources: {available}"
        )
    return provider(spec)
