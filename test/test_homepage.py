from src.homepage import _email_url, _render_topics, _sort_key


def test_topic_counts_are_ordered_by_usage():
    articles = [
        {"tags": ["Physics", "Electrodynamics"]},
        {"tags": ["physics", "Relativity"]},
        {"tags": ["Electrodynamics"]},
    ]
    html = _render_topics(articles)
    assert "Physics (2)" in html
    assert "Electrodynamics (2)" in html
    assert "Relativity (1)" in html
    assert html.index("Electrodynamics (2)") < html.index("Relativity (1)")


def test_article_dates_sort_newest_first():
    articles = [
        {"title": "Old", "date": "2026-01-01"},
        {"title": "New", "date": "2026-09-27"},
    ]
    ordered = sorted(articles, key=_sort_key, reverse=True)
    assert [article["title"] for article in ordered] == ["New", "Old"]


def test_email_address_becomes_mailto_url():
    assert _email_url("vkalita2006@gmail.com") == "mailto:vkalita2006@gmail.com"
    assert _email_url("mailto:vkalita2006@gmail.com") == "mailto:vkalita2006@gmail.com"
    assert _email_url("") == "#"
