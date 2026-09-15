"""Command-line entry point for Mark Two."""

import argparse
from pathlib import Path

from .parser import parse_file
from .renderer import render


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile a Mark Two article to HTML.")
    parser.add_argument("source", help="Path to the Mark Two source file")
    parser.add_argument("-o", "--output", default="index.html", help="Output HTML path")
    parser.add_argument(
        "--template",
        default=str(Path(__file__).resolve().parent.parent / "web" / "index.html"),
        help="HTML template path",
    )
    args = parser.parse_args()

    document = parse_file(args.source)
    output = render(document, args.template)
    Path(args.output).write_text(output, encoding="utf-8")
    print(f"Mark Two: wrote {args.output}")


if __name__ == "__main__":
    main()
