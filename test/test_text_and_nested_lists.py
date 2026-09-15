from src.ast import ListBlock, TextBlock
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


def test_text_block_supports_normal_bold_italic_and_color():
    source = '''@documenttitle{Mathematics}
@section{Test}
@text{Normal text.}
@text{bold = true, text = "Bold text."}
@text{italic = true, text = "Italic text."}
@text{bold = true, italic = true, color = red, text = "Formatted text."}
'''
    document = parse(source)
    blocks = document.sections[0].content
    assert isinstance(blocks[0], TextBlock)
    assert blocks[0].text == "Normal text."
    assert blocks[1].bold is True
    assert blocks[2].italic is True
    assert blocks[3].bold is True
    assert blocks[3].italic is True
    assert blocks[3].color == "red"


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


def test_inline_formatting_works_inside_text_blocks(tmp_path):
    source = '''@documenttitle{Mathematics}
@section{Test}
@text{This is @bold{important} and @italic{emphasized}.}
'''
    _, html = _render_source(source, tmp_path)
    assert '<strong>important</strong>' in html
    assert '<em>emphasized</em>' in html
