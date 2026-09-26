from src.parser import parse
from src.ast import TextBlock


def test_multiline_enumerate_with_commas_inside_proof():
    source = '''@documenttitle{Mathematics, banner = com_int_banner.png, color = #111111}
@section{Test}
@begin(proof)

@end(proof)
@begin(enumerate, color = green)
    @item{
        First item.
    },
    @item{
        Second item.
    }
}
'''
    document = parse(source)
    proof = document.sections[0].content[0]
    list_block = proof.content[0]
    assert proof.kind == 'proof'
    assert list_block.ordered is True
    assert list_block.color == 'green'
    assert len(list_block.items) == 2


def test_apostrophes_inside_directives():
    source = '''@documenttitle{Mathematics}
@section{Test}
@begin(theorem = Cauchy's Theorem, label = cauchy)
Cauchy's theorem is a test of ordinary apostrophes inside directive content.
@end(theorem)
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
    assert document.document_tag == 'Mathematics'
    assert document.banner == 'com_int_banner.png'
    assert document.banner_color == '#112233'
    image = document.sections[0].content[0]
    assert image.width == '60%'
    assert image.height == '200px'


def test_per_image_sizes_in_image_group():
    source = '''@documenttitle{Mathematics}
@section{Test}
@image{
    image(1) = first.png,
    image(2) = second.png,
    image(3) = third.png,
    width(1) = 50%,
    width(2) = 25%,
    height(1) = 240px,
    height(2) = 180px,
    caption = A resizable figure group.
}
'''
    document = parse(source)
    images = document.sections[0].content
    assert [image.width for image in images] == ['50%', '25%', '']
    assert [image.height for image in images] == ['240px', '180px', '']


def test_latex_like_environments_with_title_and_label():
    source = '''@documenttitle{Mathematics}
@section{Test}
Ordinary prose belongs directly to the section.

@begin(axiom = Axiom of Choice, label = choice)
This is the axiom.
@end(axiom)

@begin(theorem = Fundamental Theorem, label = fundamental)
This is the theorem.
@end(theorem)
'''
    document = parse(source)
    content = document.sections[0].content
    assert isinstance(content[0], TextBlock)
    assert content[0].text == "Ordinary prose belongs directly to the section."
    assert content[1].kind == "axiom"
    assert content[1].title == "Axiom of Choice"
    assert content[1].label == "choice"
    assert content[2].kind == "theorem"
    assert content[2].title == "Fundamental Theorem"
    assert content[2].label == "fundamental"


def test_environment_can_contain_nested_environment():
    source = '''@documenttitle{Mathematics}
@section{Test}
@begin(theorem = Main Result)
Statement of the theorem.

@begin(proof)
The proof is enclosed normally.
@end(proof)
@end(theorem)
'''
    document = parse(source)
    theorem = document.sections[0].content[0]
    assert theorem.kind == "theorem"
    assert theorem.content[0].text == "Statement of the theorem."
    assert theorem.content[1].kind == "proof"


def test_text_directive_is_removed():
    source = '''@documenttitle{Mathematics}
@section{Test}
@text{This should fail.}
'''
    try:
        parse(source)
    except ValueError as exc:
        assert "@text is no longer supported" in str(exc)
    else:
        raise AssertionError("@text should not be supported")
