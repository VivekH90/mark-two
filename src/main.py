"""Command-line entry point for Mark Two."""

import argparse
import re
import shutil
import sys
from pathlib import Path

from .bundler import inline_web_assets
from .catalog import update_catalog
from .homepage import build_homepage
from .archive import build_archive
from .parser import parse_file
from .renderer import render
from .site_config import CONFIG_FILENAME, created_artifact_path, created_artifacts_root, find_project_root, get_config, init_site, load_config, set_config


def _copy_local_image_assets(
    html: str,
    source_path: Path,
    output_path: Path,
) -> None:
    """Copy local image assets next to the generated HTML.

    Mark Two source files historically resolved image paths relative to the
    .mt file. Since generated HTML now lives under created artifacts, those
    assets must be mirrored so the same src= paths keep working.
    """
    pattern = re.compile(r'<img\\b[^>]*\\bsrc=["\\']([^"\\']+)["\\']', re.IGNORECASE)
    source_root = source_path.parent
    output_root = output_path.parent

    for raw_src in pattern.findall(html):
        src = raw_src.strip()
        if not src or src.startswith(("#", "/", "//")):
            continue
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", src):
            continue

        asset_source = (source_root / src).resolve()
        try:
            asset_source.relative_to(source_root.resolve())
        except ValueError:
            continue
        if not asset_source.is_file():
            continue

        asset_destination = (output_root / src).resolve()
        asset_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset_source, asset_destination)


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
    output_path.parent.mkdir(parents=True, exist_ok=True)

    project_root = find_project_root(source_path)
    site_config = None
    if (project_root / CONFIG_FILENAME).is_file():
        site_config = load_config(project_root)

    output = render(document, template_path, site_config=site_config)
    output = inline_web_assets(output, template_path.parent)
    output_path.write_text(output, encoding="utf-8")
    _copy_local_image_assets(output, source_path, output_path)

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
    homepage_parser = build_subparsers.add_parser("homepage", help="Build the homepage from site.json and articles.json.")
    homepage_parser.add_argument("-o", "--output", help="Homepage output path")
    homepage_parser.add_argument("--template", help="Homepage template path")
    archive_parser = build_subparsers.add_parser("archive", help="Build the full article archive.")
    archive_parser.add_argument("-o", "--output", help="Archive output path")
    archive_parser.add_argument("--template", help="Archive template path")

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

    if args.command == "build" and args.build_target == "archive":
        output = build_archive(root, output=args.output, template=args.template)
        print(f"Mark Two: wrote {output}")
        return

    if args.command == "compile":
        source_path = Path(args.source).resolve()
        project_root = find_project_root(source_path)

        if args.output:
            output_path = Path(args.output).resolve()
        else:
            output_path = created_artifact_path(source_path, project_root)

        output_path = compile_document(source_path, output_path, args.template)
        document = parse_file(source_path)
        index_path = update_catalog(
            document=document,
            source_path=source_path,
            output_path=output_path,
            index_path=args.index,
        )
        print(f"Mark Two: wrote {output_path}")
        print(f"Mark Two: updated catalog {index_path}")

        # A normal compile is the complete site update: after the document and
        # catalog are current, regenerate the site-wide homepage and archive.
        # Projects without site.json can still use Mark Two as a standalone
        # article compiler, so automatic site generation is skipped there.
        site_root = Path(index_path).resolve().parent
        if (site_root / CONFIG_FILENAME).is_file():
            homepage_output = build_homepage(
                site_root,
                output=created_artifacts_root(site_root) / "index.html",
            )
            archive_output = build_archive(
                site_root,
                output=created_artifacts_root(site_root) / "archive" / "index.html",
            )
            print(f"Mark Two: wrote {homepage_output}")
            print(f"Mark Two: wrote {archive_output}")
        else:
            print(f"Mark Two: skipped site pages (no {CONFIG_FILENAME} in {site_root})")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
