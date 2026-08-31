import textwrap
from pathlib import Path

import pytest

from scripts.generate import compile_pdf, generate, main


def _write_repo(root: Path) -> None:
    (root / "data" / "experience").mkdir(parents=True)
    (root / "profiles").mkdir()
    (root / "templates").mkdir()
    (root / "applications" / "acme-2026-01-01").mkdir(parents=True)

    (root / "data" / "experience" / "acme.yaml").write_text(
        textwrap.dedent(
            """
            company: {es: Acme, en: Acme}
            role: {es: Dev, en: Dev}
            start_date: "2022-01"
            end_date: present
            bullets:
              - id: exp-acme-1
                tags: [backend]
                text: {es: Hice cosas, en: Did things}
            """
        ),
        encoding="utf-8",
    )
    (root / "data" / "profile.yaml").write_text(
        textwrap.dedent(
            """
            name: "Test Person"
            title: {es: "Rol", en: "Role"}
            email: "test@example.com"
            phone: "000"
            summary: {es: "Resumen", en: "Summary"}
            """
        ),
        encoding="utf-8",
    )
    (root / "data" / "skills.yaml").write_text("skills: []\n", encoding="utf-8")
    (root / "data" / "projects.yaml").write_text("projects: []\n", encoding="utf-8")
    (root / "data" / "education.yaml").write_text("education: []\n", encoding="utf-8")
    (root / "data" / "certifications.yaml").write_text("certifications: []\n", encoding="utf-8")
    (root / "profiles" / "backend.yaml").write_text(
        textwrap.dedent(
            """
            name: backend
            sections:
              - type: experience
                tag_filter: [backend]
            """
        ),
        encoding="utf-8",
    )
    (root / "templates" / "ats.tex.j2").write_text(
        r"\BLOCK{for role in experience}\VAR{role.company} - \VAR{role.role}"
        r"\BLOCK{for b in role.bullets}"
        "\n"
        r"\VAR{b}\BLOCK{endfor}\BLOCK{endfor}",
        encoding="utf-8",
    )
    (root / "applications" / "acme-2026-01-01" / "config.yaml").write_text(
        textwrap.dedent(
            """
            company: Acme
            profile: backend
            template: ats
            lang: es
            """
        ),
        encoding="utf-8",
    )


def test_generate_writes_tex_file_with_rendered_content(tmp_path):
    _write_repo(tmp_path)

    tex_path = generate("acme-2026-01-01", repo_root=tmp_path, compile=False)

    assert tex_path == tmp_path / "applications" / "acme-2026-01-01" / "cv.tex"
    content = tex_path.read_text(encoding="utf-8")
    assert "Acme" in content
    assert "Hice cosas" in content


def test_generate_raises_when_validation_fails(tmp_path):
    _write_repo(tmp_path)
    experience_file = tmp_path / "data" / "experience" / "acme.yaml"
    experience_file.write_text(
        experience_file.read_text(encoding="utf-8")
        + "  - id: exp-acme-1\n    tags: [backend]\n    text: {es: Otro, en: Other}\n",
        encoding="utf-8",
    )

    try:
        generate("acme-2026-01-01", repo_root=tmp_path, compile=False)
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "exp-acme-1" in str(exc)


def test_generate_raises_on_unknown_section_type(tmp_path):
    _write_repo(tmp_path)
    # An unrecognised section type must fail loudly instead of silently
    # dropping the whole section from the rendered CV.
    (tmp_path / "profiles" / "backend.yaml").write_text(
        textwrap.dedent(
            """
            name: backend
            sections:
              - type: experience
                tag_filter: [backend]
              - type: publications
            """
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="publications"):
        generate("acme-2026-01-01", repo_root=tmp_path, compile=False)


def test_generate_certifications_section_resolves_lang_and_badge_path(tmp_path):
    _write_repo(tmp_path)

    # Create a minimal badge image file (1x1 transparent PNG)
    (tmp_path / "assets" / "badges").mkdir(parents=True)
    (tmp_path / "assets" / "badges" / "aws.png").write_bytes(
        bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a49444154785e6300010000050001e1a18f2a0000000049454e44ae426082")
    )

    (tmp_path / "data" / "certifications.yaml").write_text(
        textwrap.dedent(
            """
            certifications:
              - id: cert-aws
                tags: [cloud]
                name: {es: "AWS Solutions Architect", en: "AWS Solutions Architect"}
                issuer: "Amazon Web Services"
                date: "2023-05"
                badge_image: assets/badges/aws.png
            """
        ),
        encoding="utf-8",
    )
    (tmp_path / "profiles" / "backend.yaml").write_text(
        textwrap.dedent(
            """
            name: backend
            sections:
              - type: experience
                tag_filter: [backend]
              - type: certifications
                tag_filter: [cloud]
            """
        ),
        encoding="utf-8",
    )
    (tmp_path / "templates" / "visual.tex.j2").write_text(
        r"\BLOCK{for cert in certifications}"
        r"\includegraphics{\VAR{cert.badge_image}} \VAR{cert.name}"
        r"\BLOCK{endfor}",
        encoding="utf-8",
    )
    (tmp_path / "applications" / "acme-2026-01-01" / "config.yaml").write_text(
        textwrap.dedent(
            """
            company: Acme
            profile: backend
            template: visual
            lang: es
            """
        ),
        encoding="utf-8",
    )

    tex_path = generate("acme-2026-01-01", repo_root=tmp_path, compile=False)

    content = tex_path.read_text(encoding="utf-8")
    # Badge image should use relative path (../../assets/badges/aws.png)
    assert "../../assets/badges/aws.png" in content
    # Verify no absolute paths are baked in
    assert ":\\" not in content  # no Windows absolute path
    assert "C:/" not in content  # no absolute path in posix form
    assert "AWS Solutions Architect" in content


def test_compile_pdf_error_includes_both_stdout_and_stderr(monkeypatch, tmp_path):
    # latexmk writes fatal errors to stderr; dropping that stream leaves whoever
    # hits a compile failure with a useless message.
    import subprocess

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout="latexmk log noise\nsome stdout detail",
            stderr="Fatal error occurred, no output PDF file produced!",
        )

    monkeypatch.setattr("scripts.generate.subprocess.run", fake_run)
    tex_path = tmp_path / "cv.tex"
    tex_path.write_text("", encoding="utf-8")

    with pytest.raises(RuntimeError) as excinfo:
        compile_pdf(tex_path)

    message = str(excinfo.value)
    assert "some stdout detail" in message
    assert "Fatal error occurred, no output PDF file produced!" in message


def test_main_reports_non_runtime_errors_cleanly(monkeypatch, capsys):
    # A missing application folder raises FileNotFoundError, not RuntimeError:
    # the CLI boundary must still print a message and exit 1, never traceback.
    monkeypatch.setattr("sys.argv", ["generate.py", "no-such-application", "--no-compile"])

    exit_code = main()

    assert exit_code == 1
    assert capsys.readouterr().out.strip() != ""
