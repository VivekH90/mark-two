from src.ast import ListBlock
from src.parser import parse
from src.renderer import render


def _render_source(source, tmp_path):
    document = parse(source)
    template = tmp_path / "template.html"
    template.write_text("{{ARTICLE}}", encoding="utf-8")
    return document, render(document, template)


def test_nested_enumerate_is_nested_and_renders_as_letters(tmp_path):
    source = '''@documenttitle{Mathematics}
@section{Test}
@enumerate{
    @item{
        First item.
        @enumerate{
            @item{First sub-item.},
            @item{Second sub-item.}
        }
    },
    @item{Second item.}
}
'''
    document, html = _render_source(source, tmp_path)
    outer = document.sections[0].content[0]
    inner = outer.items[0].content[1]
    assert isinstance(outer, ListBlock)
    assert isinstance(inner, ListBlock)
    assert outer.ordered is True
    assert inner.ordered is True
    assert '<ol class="mark-list"' in html
    assert 'type="a"' in html


def test_inline_formatting_can_begin_a_line(tmp_path):
    source = '''@documenttitle{Mathematics}
@section{Test}
@bold{This entire line is bold.}
@italic{This entire line is italic.}
@color{red, This entire line is red.}
'''
    _, html = _render_source(source, tmp_path)
    assert '<strong>This entire line is bold.</strong>' in html
    assert '<em>This entire line is italic.</em>' in html
    assert 'color: red' in html


def test_inline_formatting_is_recursive_and_html_escaped(tmp_path):
    source = '''@documenttitle{Mathematics}
@section{Test}
Normal @bold{bold} and @italic{italic} text.
This is @bold{very @italic{important}}.
This is @color{red, @bold{extremely important}}.
This is @color{color = #315a9b, text = "blue text"}.
This is <unsafe> & safe.
'''
    _, html = _render_source(source, tmp_path)
    assert '<strong>bold</strong>' in html
    assert '<em>italic</em>' in html
    assert '<strong>very <em>important</em></strong>' in html
    assert 'color: red' in html
    assert '<strong>extremely important</strong>' in html
    assert 'color: #315a9b' in html
    assert '&lt;unsafe&gt; &amp; safe.' in html


def test_environment_numbering_is_shared_within_each_section(tmp_path):
    source = """@documenttitle{Mathematics}
@section{First}
@begin(theorem = A)
Statement.
@end(theorem)
@begin(proposition = B)
Statement.
@end(proposition)

@section{Second}
@begin(definition = C)
Definition.
@end(definition)
"""
    _, html = _render_source(source, tmp_path)
    assert "Theorem 1.1" in html
    assert "Proposition 1.2" in html
    assert "Definition 2.1" in html


def test_article_template_contains_progress_bar(tmp_path):
    from pathlib import Path
    template = Path("web/index.html").read_text(encoding="utf-8")
    script = Path("web/script.js").read_text(encoding="utf-8")
    style = Path("web/style.css").read_text(encoding="utf-8")
    assert '<div id="bar" aria-hidden="true"></div>' in template
    assert "getElementById('bar')" in script
    assert "background:var(--accent2)" in style
    assert ".proto{" in style


def test_display_math_html_escapes_comparison_and_alignment_characters(tmp_path):
    source = r'''@documenttitle{Mathematics}
@section{Test}
[
a < b,qquad c > d
]

[
\begin{aligned}
A & = B \\
C & = D
\end{aligned}
]
'''
    _, html = _render_source(source, tmp_path)
    assert r"\[a &lt; b,\qquad c &gt; d\]" in html
    assert r"\begin{aligned}" in html
    assert "&amp; = B" in html
    assert "A &amp; = B" in html
