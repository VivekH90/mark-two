"""Command-line entry point for Mark Two."""

import argparse
import shutil
import sys
from pathlib import Path

from .catalog import update_catalog
from .gallery import resolve_gallery
from .homepage import build_homepage
from .parser import parse_file
from .renderer import render
from .site_config import find_project_root, get_config, init_site, set_config


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
    mark_two_root = Path(__file__).resolve().parent.parent
    default_template = mark_two_root / "web" / "index.html"

    parser = argparse.ArgumentParser(
        description="Build websites from Mark Two source files."
    )
    subparsers = parser.add_subparsers(dest="command")

    compile_parser = subparsers.add_parser("compile", help="Compile one Mark Two article into HTML.")
    compile_parser.add_argument("source", help="Path to the Mark Two source file")
    compile_parser.add_argument("-o", "--output", help="Output HTML path")
    compile_parser.add_argument("--template", default=str(default_template), help="HTML template path")
    compile_parser.add_argument("--index", help="Article catalog path")

    init_parser = subparsers.add_parser("init", help="Initialize a Mark Two site configuration.")
    init_parser.add_argument("--force", action="store_true", help="Replace an existing site.json")

    config_parser = subparsers.add_parser("config", help="Read or change site configuration.")
    config_subparsers = config_parser.add_subparsers(dest="config_command")
    config_set = config_subparsers.add_parser("set", help="Set a configuration value")
    config_set.add_argument("key", help="Configuration key")
    config_set.add_argument("value", help="Configuration value")
    config_get = config_subparsers.add_parser("get", help="Get a configuration value")
    config_get.add_argument("key", nargs="?", help="Configuration key")

    build_parser = subparsers.add_parser("build", help="Build generated site pages.")
    build_subparsers = build_parser.add_subparsers(dest="build_target")
    homepage_parser = build_subparsers.add_parser(
        "homepage",
        help="Build the homepage from site.json and articles.json.",
    )
    homepage_parser.add_argument("-o", "--output", help="Homepage output path")
    homepage_parser.add_argument("--template", help="Homepage template path")

    known_commands = {"compile", "init", "config", "build", "-h", "--help"}
    if len(sys.argv) > 1 and sys.argv[1] not in known_commands:
        sys.argv.insert(1, "compile")

    args = parser.parse_args()
    root = find_project_root()

    if args.command == "init":
        path = init_site(root, force=args.force)
        print(f"Mark Two: initialized {path}")
        return

    if args.command == "config":
        if args.config_command == "set":
            path = set_config(root, args.key, args.value)
            print(f"Mark Two: updated {path}")
            return
        if args.config_command == "get":
            value = get_config(root, args.key)
            if isinstance(value, dict):
                import json
                print(json.dumps(value, indent=2, ensure_ascii=False))
            else:
                print(value)
            return
        config_parser.print_help()
        return

    if args.command == "build" and args.build_target == "homepage":
        output = build_homepage(root, output=args.output, template=args.template)
        print(f"Mark Two: wrote {output}")
        return

    if args.command == "compile":
        source_path = Path(args.source).resolve()
        output_path = Path(args.output).resolve() if args.output else source_path.parent / "index.html"
        output_path = compile_document(source_path, output_path, args.template)
        document = parse_file(source_path)
        index_path = update_catalog(
            document=document,
            source_path=source_path,
            output_path=output_path,
            index_path=args.index,
        )
        print(f"Mark Two: wrote {output_path}")
        print(f"Mark Two: assets copied to {output_path.parent}")
        print(f"Mark Two: updated catalog {index_path}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
