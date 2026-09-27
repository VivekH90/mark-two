from src.homepage import _render_topics, _sort_key


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
