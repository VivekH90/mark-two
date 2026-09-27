from pathlib import Path

from src.bundler import inline_web_assets


def test_inline_web_assets(tmp_path: Path):
    (tmp_path / "style.css").write_text("body { color: red; }", encoding="utf-8")
    (tmp_path / "script.js").write_text("console.log('ok');", encoding="utf-8")

    html = (
        '<head><link rel="stylesheet" href="style.css"></head>'
        '<body><script src="script.js"></script></body>'
    )
    bundled = inline_web_assets(html, tmp_path)

    assert '<link rel="stylesheet" href="style.css">' not in bundled
    assert '<script src="script.js"></script>' not in bundled
    assert "<style>\nbody { color: red; }\n</style>" in bundled
    assert "<script>\nconsole.log('ok');\n</script>" in bundled


def test_external_assets_are_preserved(tmp_path: Path):
    (tmp_path / "style.css").write_text("body {}", encoding="utf-8")
    (tmp_path / "script.js").write_text("void 0;", encoding="utf-8")

    html = (
        '<link rel="stylesheet" href="style.css">'
        '<script src="https://example.com/library.js"></script>'
    )
    bundled = inline_web_assets(html, tmp_path)

    assert "https://example.com/library.js" in bundled
    assert "<style>" in bundled
