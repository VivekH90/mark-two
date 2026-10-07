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



def test_topic_list_is_limited_to_five():
    articles = [
        {"tags": ["Tag A"]},
        {"tags": ["Tag B"]},
        {"tags": ["Tag C"]},
        {"tags": ["Tag D"]},
        {"tags": ["Tag E"]},
        {"tags": ["Tag F"]},
    ]
    html = _render_topics(articles)
    assert "Tag A (1)" in html
    assert "Tag E (1)" in html
    assert "Tag F (1)" not in html


def test_recent_cards_expose_document_type():
    from src.homepage import _render_recent
    html = _render_recent([
        {"title": "A Note", "doctype": "notes", "date": "2026-10-01"},
        {"title": "An Article", "doctype": "article", "date": "2026-09-01"},
    ])
    assert 'data-doctype="notes"' in html
    assert 'data-doctype="article"' in html
    assert "Notes" in html
    assert "Article" in html
