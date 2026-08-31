import textwrap
from pathlib import Path

from scripts.generate import generate


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
