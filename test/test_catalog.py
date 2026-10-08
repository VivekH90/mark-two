from pathlib import Path

from src.ast import Document, Section
from src.catalog import build_catalog_entry, update_catalog


def test_catalog_entry_contains_homepage_and_search_metadata(tmp_path):
    root = tmp_path / "site"
    source = root / "physics" / "electromagnetism" / "fields.mt"
    output = root / "physics" / "electromagnetism" / "fields" / "index.html"
    source.parent.mkdir(parents=True)
    document = Document(
        document_tag="Physics",
        doctype="notes",
        folder="Electromagnetism",
        author="Vivek Sharma",
        article_title="Field Equations",
        description="A derivation of the electromagnetic field equations.",
        date="27 September 2026",
        tags=["Electromagnetism", " field theory ", "Electromagnetism"],
        sections=[Section(title="Maxwell's Equations")],
    )

    entry = build_catalog_entry(document, source, output, root)

    assert entry["id"] == "physics/electromagnetism/fields"
    assert entry["doctype"] == "notes"
    assert entry["title"] == "Field Equations"
    assert entry["description"] == "A derivation of the electromagnetic field equations."
    assert entry["subject"] == "Physics"
    assert entry["folder"] == "Electromagnetism"
    assert entry["tags"] == ["Electromagnetism", "field theory"]
    assert entry["url"] == "/physics/electromagnetism/fields/"
    assert entry["source"] == "physics/electromagnetism/fields.mt"
    assert entry["sections"] == ["Maxwell's Equations"]


def test_update_catalog_replaces_only_matching_article(tmp_path):
    root = tmp_path / "site"
    catalog = root / "articles.json"
    source_a = root / "a.mt"
    source_b = root / "b.mt"
    output_a = root / "a" / "index.html"
    output_b = root / "b" / "index.html"
    source_a.parent.mkdir(parents=True)

    document_a = Document(article_title="Article A")
    document_b = Document(article_title="Article B", tags=["Updated"])

    update_catalog(document_a, source_a, output_a, catalog)
    update_catalog(document_b, source_b, output_b, catalog)

    document_a_updated = Document(article_title="Article A Updated", tags=["New"])
    update_catalog(document_a_updated, source_a, output_a, catalog)

    data = __import__("json").loads(catalog.read_text(encoding="utf-8"))
    assert [article["id"] for article in data["articles"]] == ["a", "b"]
    assert data["articles"][0]["title"] == "Article A Updated"
    assert data["articles"][0]["tags"] == ["New"]
    assert data["articles"][1]["title"] == "Article B"


def test_update_catalog_does_not_rewrite_identical_catalog(tmp_path):
    root = tmp_path / "site"
    catalog = root / "articles.json"
    source = root / "a.mt"
    output = root / "a" / "index.html"
    source.parent.mkdir(parents=True)

    document = Document(article_title="Article A")
    update_catalog(document, source, output, catalog)
    first_contents = catalog.read_text(encoding="utf-8")

    update_catalog(document, source, output, catalog)
    assert catalog.read_text(encoding="utf-8") == first_contents


def test_resources_source_keeps_public_url_clean(tmp_path):
    root = tmp_path / "site"
    source = root / "resources" / "mathematics" / "analysis" / "density" / "density.mt"
    output = root / "created artifacts" / "mathematics" / "analysis" / "density" / "index.html"
    source.parent.mkdir(parents=True)

    entry = build_catalog_entry(
        Document(article_title="Density"),
        source,
        output,
        root,
    )

    assert entry["source"] == "resources/mathematics/analysis/density/density.mt"
    assert entry["url"] == "/mathematics/analysis/density/"



def test_catalog_strips_created_artifacts_from_public_url(tmp_path):
    root = tmp_path / "site"
    source = root / "completeness" / "completeness.mt"
    output = root / "created artifacts" / "completeness" / "index.html"
    source.parent.mkdir(parents=True)

    entry = build_catalog_entry(
        Document(article_title="Completeness"),
        source,
        output,
        root,
    )

    assert entry["url"] == "/completeness/"
