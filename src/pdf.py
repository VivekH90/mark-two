"""LaTeX-to-PDF compilation for Mark Two."""

from __future__ import annotations

import os
import shutil
import subprocess
import sysconfig
import tempfile
from pathlib import Path


def find_latex_style_dir(mark_two_root: str | Path) -> Path:
    """Locate Mark Two's bundled LaTeX style package."""
    root = Path(mark_two_root).resolve()
    candidates = [
        root / "templates" / "latex",
        Path(sysconfig.get_path("data")) / "share" / "mark-two" / "templates" / "latex",
    ]
    for candidate in candidates:
        if (candidate / "marktwo.sty").is_file():
            return candidate
    searched = "\\n".join(str(path) for path in candidates)
    raise FileNotFoundError(
        "Mark Two's LaTeX package (marktwo.sty) could not be found. "
        f"Searched:\\n{searched}"
    )


def compile_pdf(
    source_path: str | Path,
    output_path: str | Path,
    style_dir: str | Path,
    engine: str = "pdflatex",
) -> Path:
    """Compile a .tex file and keep every TeX auxiliary file out of the project.

    LaTeX is run twice so the table of contents and cross-references settle.
    Its complete working output is isolated in a temporary directory; only
    the final PDF is copied to the requested artifact path.
    """
    source = Path(source_path).resolve()
    output = Path(output_path).resolve()
    styles = Path(style_dir).resolve()

    if source.suffix.lower() != ".tex":
        raise ValueError(f"Expected a .tex source file, got: {source}")
    if not source.is_file():
        raise FileNotFoundError(f"LaTeX source file not found: {source}")
    if output.suffix.lower() != ".pdf":
        raise ValueError(f"PDF output path must end in .pdf: {output}")
    if not (styles / "marktwo.sty").is_file():
        raise FileNotFoundError(f"Mark Two LaTeX style not found: {styles / 'marktwo.sty'}")

    executable = shutil.which(engine)
    if executable is None:
        raise FileNotFoundError(
            f"Could not find '{engine}'. Install a TeX distribution with pdfLaTeX "
            "and make sure it is available on PATH."
        )

    environment = os.environ.copy()
    existing_texinputs = environment.get("TEXINPUTS", "")
    texinputs = [str(styles) + "//"]
    if existing_texinputs:
        texinputs.append(existing_texinputs)
    environment["TEXINPUTS"] = os.pathsep.join(texinputs) + os.pathsep

    with tempfile.TemporaryDirectory(prefix="mark-two-latex-") as temporary:
        work_output = Path(temporary)
        command = [
            executable,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            "-synctex=0",
            f"-output-directory={work_output}",
            source.name,
        ]

        for pass_number in (1, 2):
            result = subprocess.run(
                command,
                cwd=source.parent,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                log = (result.stdout or "") + (result.stderr or "")
                excerpt = "\\n".join(log.splitlines()[-35:])
                raise RuntimeError(
                    f"LaTeX compilation failed on pass {pass_number} for {source}.\\n"
                    f"{excerpt}"
                )

        generated_pdf = work_output / f"{source.stem}.pdf"
        if not generated_pdf.is_file():
            raise RuntimeError(
                f"LaTeX finished without producing the expected PDF: {generated_pdf}"
            )

        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(generated_pdf, output)

    return output
