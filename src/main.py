"""Command-line entry point for Mark Two."""

import argparse
import shutil
from pathlib import Path

from .gallery import resolve_gallery
from .parser import parse_file
from .renderer import render


def compile_document(
    source_path: str | Path,
    output_path: str | Path,
    template_path: str | Path,
) -> Path:
    """Compile a Mark Two source file into a self-contained web bundle.

    The generated HTML, CSS, and JavaScript are placed in the same output
    directory so relative asset paths work when the result is opened or
    served locally.
    """
    source_path = Path(source_path).resolve()
    output_path = Path(output_path).resolve()
    template_path = Path(template_path).resolve()

    document = parse_file(source_path)
    if document.gallery is not None:
        document.gallery_items = resolve_gallery(document.gallery)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output = render(document, template_path)
    output_path.write_text(output, encoding="utf-8")

    asset_dir = template_path.parent
    for asset_name in ("style.css", "script.js"):
        source_asset = asset_dir / asset_name
        if not source_asset.is_file():
            raise FileNotFoundError(
                f"Required template asset not found: {source_asset}"
            )
        shutil.copy2(source_asset, output_path.parent / asset_name)

    return output_path


def main() -> None:
    # main.py lives in <mark-two>/src/, so this remains valid even when the
    # command is launched from a completely different working directory.
    mark_two_root = Path(__file__).resolve().parent.parent
    default_template = mark_two_root / "web" / "index.html"

    parser = argparse.ArgumentParser(
        description="Compile a Mark Two article to a self-contained HTML bundle."
    )
    parser.add_argument("source", help="Path to the Mark Two source file")
    parser.add_argument(
        "-o",
        "--output",
        help="Output HTML path (default: index.html beside the source file)",
    )
    parser.add_argument(
        "--template",
        default=str(default_template),
        help="HTML template path (default: Mark Two's built-in template)",
    )
    args = parser.parse_args()

    source_path = Path(args.source).resolve()
    output_path = Path(args.output).resolve() if args.output else source_path.parent / "index.html"

    output_path = compile_document(source_path, output_path, args.template)
    print(f"Mark Two: wrote {output_path}")
    print(f"Mark Two: assets copied to {output_path.parent}")


if __name__ == "__main__":
    main()
