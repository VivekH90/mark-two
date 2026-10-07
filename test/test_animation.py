from pathlib import Path

from src.ast import Animation
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
