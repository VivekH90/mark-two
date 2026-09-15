from src.ast import ListBlock, TextBlock
from src.parser import parse
from src.renderer import render


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
    document = parse(source)
    outer = document.sections[0].content[0]
    inner = outer.items[0].content[1]
    assert isinstance(outer, ListBlock)
    assert isinstance(inner, ListBlock)
    assert outer.ordered is True
    assert inner.ordered is True

    template = tmp_path / "template.html"
    template.write_text("{{ARTICLE}}", encoding="utf-8")
    html = render(document, template)
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
