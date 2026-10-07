from pathlib import Path

from src.ast import Animation, Environment
from src.parser import parse
from src.renderer import render


def test_animation_body_is_raw_and_preserves_code_syntax():
    source = r'''@documenttitle{Physics}
@section{Interactive Proof}
Before the animation.

@begin(animation)

<div class="demo">
  <canvas id="demo-canvas"></canvas>
</div>

<style>
@keyframes pulse {
  from { transform: scale(1); }
  to { transform: scale(1.1); }
}
@media (max-width: 600px) {
  .demo { width: 100%; }
}
</style>

<script>
const state = { value: 1 };
function step() {
  return state.value + 1;
}
</script>

@end(animation)

After the animation.
'''
    document = parse(source)
    content = document.sections[0].content

    assert len(content) == 3
    assert isinstance(content[1], Animation)
    assert "@keyframes pulse" in content[1].content
    assert "const state = { value: 1 };" in content[1].content
    assert "function step()" in content[1].content


def test_animation_renders_inside_mark_two_shell():
    source = r'''@documenttitle{Physics}
@section{Interactive Proof}
@begin(animation, label = demo-animation)
<canvas id="canvas"></canvas>
<style>
#canvas { width: 100%; }
</style>
<script>
document.getElementById("canvas");
</script>
@end(animation)
'''
    document = parse(source)
    template = Path(__file__).parents[1] / "web" / "index.html"
    html = render(document, template)

    assert '<div class="mt-animation" data-mark-two-animation="true" id="demo-animation">' in html
    assert '<canvas id="canvas"></canvas>' in html
    assert '<style>' in html
    assert '<script>' in html
    assert 'document.getElementById("canvas");' in html


def test_multiple_animations_and_normal_environments_can_coexist():
    source = r'''@documenttitle{Mathematics}
@section{Proof}
@begin(theorem = A Theorem)
Statement.
@end(theorem)

@begin(animation, label = first)
<div id="first"></div>
<script>
const first = { value: 1 };
</script>
@end(animation)

@begin(proof)
The proof continues.
@begin(animation, label = second)
<div id="second"></div>
<style>
@media (max-width: 700px) { #second { width: 100%; } }
</style>
@end(animation)
@end(proof)
'''
    document = parse(source)
    content = document.sections[0].content

    assert isinstance(content[0], Environment)
    assert isinstance(content[1], Animation)
    assert isinstance(content[2], Environment)
    assert isinstance(content[2].content[1], Animation)
    assert content[1].label == "first"
    assert content[2].content[1].label == "second"


def test_animation_rejects_unknown_arguments():
    source = '''@documenttitle{Mathematics}
@section{Test}
@begin(animation = Not Allowed)
@end(animation)
'''
    import pytest
    with pytest.raises(ValueError, match="accepts no title"):
        parse(source)
