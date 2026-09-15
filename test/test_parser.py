from src.parser import parse


def test_multiline_enumerate_with_commas():
    source = '''@documenttitle{Mathematics, banner = com_int_banner.png, color = #111111}
@section{Test}
@proof{}
@enumerate{color = green,
    @item{
        First item.
    },
    @item{
        Second item.
    }
}
'''
    document = parse(source)
    list_block = document.sections[0].content[1]
    assert list_block.ordered is True
    assert list_block.color == 'green'
    assert len(list_block.items) == 2


def test_apostrophes_inside_directives():
    source = '''@documenttitle{Mathematics}
@section{Test}
@theorem{Cauchy's Theorem, label = cauchy}
Cauchy's theorem is a test of ordinary apostrophes inside directive content.
'''
    document = parse(source)
    theorem = document.sections[0].content[0]
    assert theorem.title == "Cauchy's Theorem"
    assert theorem.label == 'cauchy'


def test_multiline_image_and_documenttitle():
    source = '''@documenttitle{
    Mathematics,
    banner = com_int_banner.png,
    color = #112233
}
@section{Test}
@image{
    src = figure.png,
    width = 60%,
    height = 200px,
    caption = A figure
}
'''
    document = parse(source)
    assert document.document_title == 'Mathematics'
    assert document.banner == 'com_int_banner.png'
    assert document.banner_color == '#112233'
    image = document.sections[0].content[0]
    assert image.width == '60%'
    assert image.height == '200px'
