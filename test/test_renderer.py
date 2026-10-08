from src.ast import Document, Button, Section
from src.renderer import render


def test_site_navigation_is_generated_from_config(tmp_path):
    template = tmp_path / "index.html"
    template.write_text("{{BUTTONS}}", encoding="utf-8")

    document = Document(
        article_title="Test",
        buttons=[
            Button(name="Home", href="/wrong-home", color="red"),
            Button(name="Custom", href="/custom", color="blue"),
        ],
        sections=[Section(title="Test")],
    )

    html = render(
        document,
        template,
        site_config={
            "archive": "/archive/",
            "about": "/about/",
            "github": "https://github.com/example/project",
        },
    )

    assert 'href="/"' in html
    assert 'href="/archive/"' in html
    assert 'href="/about/"' in html
    assert 'href="https://github.com/example/project"' in html
    assert 'href="/custom"' in html
    assert 'href="/wrong-home"' not in html
    assert html.count(">Home</a>") == 1
    assert html.count(">Archive</a>") == 1
    assert html.count(">About</a>") == 1
    assert html.count(">GitHub</a>") == 1


def test_site_navigation_has_defaults_without_site_config(tmp_path):
    template = tmp_path / "index.html"
    template.write_text("{{BUTTONS}}", encoding="utf-8")

    document = Document(
        article_title="Test",
        sections=[Section(title="Test")],
    )

    html = render(document, template)

    assert 'href="/"' in html
    assert 'href="/archive/"' in html
    assert 'href="/about/"' in html
    assert ">GitHub</a>" not in html
