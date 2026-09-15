"""Command-line entry point for Mark Two."""

import argparse
import shutil
from pathlib import Path

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
    source_path = Path(source_path)
    output_path = Path(output_path)
    template_path = Path(template_path)

    document = parse_file(source_path)
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
    project_root = Path(__file__).resolve().parent.parent
    default_template = project_root / "web" / "index.html"
    default_output = project_root / "build" / "index.html"

    parser = argparse.ArgumentParser(
        description="Compile a Mark Two article to a self-contained HTML bundle."
    )
    parser.add_argument("source", help="Path to the Mark Two source file")
    parser.add_argument(
        "-o",
        "--output",
        default=str(default_output),
        help="Output HTML path (default: build/index.html)",
    )
    parser.add_argument(
        "--template",
        default=str(default_template),
        help="HTML template path",
    )
    args = parser.parse_args()

    output_path = compile_document(args.source, args.output, args.template)
    print(f"Mark Two: wrote {output_path}")
    print(f"Mark Two: assets copied to {output_path.parent}")


if __name__ == "__main__":
    main()
