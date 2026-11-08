from pathlib import Path

import pytest

import src.pdf as pdf


def test_created_pdf_artifact_path_mirrors_resources_tree(tmp_path):
    from src.site_config import created_pdf_artifact_path

    root = tmp_path / "site"
    source = (
        root / "resources" / "physics" / "radiation" / "radiation.tex"
    )
    assert created_pdf_artifact_path(source, root) == (
        root / "created artifacts" / "physics" / "radiation" / "index.pdf"
    )


def test_root_level_tex_sources_get_separate_pdf_artifacts(tmp_path):
    from src.site_config import created_pdf_artifact_path

    root = tmp_path / "site"
    assert created_pdf_artifact_path(root / "paper.tex", root) == (
        root / "created artifacts" / "paper" / "index.pdf"
    )


def test_tex_sources_cannot_live_inside_created_artifacts(tmp_path):
    from src.site_config import created_pdf_artifact_path

    root = tmp_path / "site"
    source = root / "created artifacts" / "bad.tex"
    with pytest.raises(ValueError):
        created_pdf_artifact_path(source, root)


def test_compile_pdf_keeps_only_pdf_in_destination_and_cleans_temp_files(
    tmp_path, monkeypatch
):
    source = tmp_path / "paper.tex"
    source.write_text(
        r"\documentclass{article}\begin{document}Test\end{document}",
        encoding="utf-8",
    )
    styles = tmp_path / "styles"
    styles.mkdir()
    (styles / "marktwo.sty").write_text("% test package", encoding="utf-8")
    destination = tmp_path / "created artifacts" / "paper" / "index.pdf"
    temporary_dirs = []

    monkeypatch.setattr(pdf.shutil, "which", lambda engine: "/usr/bin/pdflatex")

    def fake_run(command, cwd, env, capture_output, text, check):
        output_arg = next(arg for arg in command if arg.startswith("-output-directory="))
        output_dir = Path(output_arg.split("=", 1)[1])
        temporary_dirs.append(output_dir)
        (output_dir / "paper.pdf").write_bytes(b"%PDF-test")
        (output_dir / "paper.aux").write_text("aux")
        (output_dir / "paper.log").write_text("log")
        (output_dir / "paper.fls").write_text("fls")
        (output_dir / "paper.out").write_text("out")
        (output_dir / "paper.fdb_latexmk").write_text("fdb")
        return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(pdf.subprocess, "run", fake_run)

    result = pdf.compile_pdf(source, destination, styles)

    assert result == destination
    assert destination.read_bytes() == b"%PDF-test"
    source_pdf = source.with_suffix(".pdf")
    assert source_pdf.read_bytes() == b"%PDF-test"
    assert source_pdf.parent == source.parent
    assert len(temporary_dirs) == 2
    assert all(not directory.exists() for directory in temporary_dirs)
    assert sorted(path.name for path in destination.parent.iterdir()) == ["index.pdf"]
