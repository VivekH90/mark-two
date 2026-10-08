import sys

from pathlib import Path

import src.main as main


def test_compile_rebuilds_homepage_and_archive(tmp_path, monkeypatch):
    source = tmp_path / "article.mt"
    output = tmp_path / "article" / "index.html"
    source.write_text("@section{Test}\n", encoding="utf-8")
    (tmp_path / "site.json").write_text("{}\n", encoding="utf-8")

    calls = []

    monkeypatch.setattr(main, "find_project_root", lambda *_: tmp_path)
    monkeypatch.setattr(main, "compile_document", lambda source, output, template: calls.append(("compile", Path(source), Path(output))) or Path(output))
    monkeypatch.setattr(main, "parse_file", lambda source: "document")
    monkeypatch.setattr(main, "update_catalog", lambda **kwargs: calls.append(("catalog", kwargs["index_path"])) or tmp_path / "articles.json")
    monkeypatch.setattr(main, "build_homepage", lambda root: calls.append(("homepage", root)) or root / "index.html")
    monkeypatch.setattr(main, "build_archive", lambda root: calls.append(("archive", root)) or root / "archive" / "index.html")

    monkeypatch.setattr(
        sys,
        "argv",
        ["mark-two", str(source), "--output", str(output)],
    )

    main.main()

    assert [kind for kind, *_ in calls] == ["compile", "catalog", "homepage", "archive"]
    assert calls[-1][1] == tmp_path


def test_root_level_sources_get_separate_artifact_directories(tmp_path):
    from src.site_config import created_artifact_path

    root = tmp_path / "site"
    root.mkdir()
    assert created_artifact_path(root / "a.mt", root) == root / "created artifacts" / "a" / "index.html"
    assert created_artifact_path(root / "b.mt", root) == root / "created artifacts" / "b" / "index.html"

def test_resources_path_is_not_part_of_public_artifact_tree(tmp_path):
    from src.site_config import created_artifact_path

    root = tmp_path / "site"
    source = (
        root
        / "resources"
        / "mathematics"
        / "analysis"
        / "real-analysis"
        / "rational-density"
        / "density.mt"
    )

    assert created_artifact_path(source, root) == (
        root
        / "created artifacts"
        / "mathematics"
        / "analysis"
        / "real-analysis"
        / "rational-density"
        / "index.html"
    )


def test_sources_cannot_live_inside_created_artifacts(tmp_path):
    from src.site_config import created_artifact_path
    import pytest

    root = tmp_path / "site"
    source = root / "created artifacts" / "bad.mt"
    with pytest.raises(ValueError):
        created_artifact_path(source, root)


def test_generated_page_path_honors_local_archive_url(tmp_path):
    from src.site_config import generated_page_path

    assert generated_page_path(tmp_path, "/writing/archive/", "/archive/") == (
        tmp_path / "created artifacts" / "writing" / "archive" / "index.html"
    )
