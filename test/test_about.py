from src.about import build_about


def test_about_page_is_generated(tmp_path):
    (tmp_path / "site.json").write_text('{"author":"Vivek","about":"/about/","archive":"/archive/","github":"https://github.com/Vivek"}', encoding="utf-8")
    output = build_about(tmp_path)
    assert output == tmp_path / "created artifacts" / "about" / "index.html"
    html = output.read_text(encoding="utf-8")
    assert "Vivek" in html
    assert "../" in html
