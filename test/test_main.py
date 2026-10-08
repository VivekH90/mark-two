import sys

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
