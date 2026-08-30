import textwrap
from pathlib import Path

from scripts.validate import run_validation


def _write_minimal_repo(root: Path) -> None:
    (root / "data" / "experience").mkdir(parents=True)
    (root / "profiles").mkdir()
    (root / "applications" / "acme-2026-01-01").mkdir(parents=True)

    (root / "data" / "experience" / "acme.yaml").write_text(
        textwrap.dedent(
            """
            company: {es: Acme, en: Acme}
            role: {es: Dev, en: Dev}
            bullets:
              - id: exp-acme-1
                tags: [backend]
                text: {es: Hola, en: Hello}
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
    (root / "applications" / "acme-2026-01-01" / "config.yaml").write_text(
        textwrap.dedent(
            """
            company: Acme
            profile: backend
            lang: es
            overrides:
              include_bullets: [exp-acme-1]
            """
        ),
        encoding="utf-8",
    )


def test_run_validation_passes_on_consistent_minimal_repo(tmp_path):
    _write_minimal_repo(tmp_path)
    assert run_validation(tmp_path) == []


def test_run_validation_catches_duplicate_id(tmp_path):
    _write_minimal_repo(tmp_path)
    experience_file = tmp_path / "data" / "experience" / "acme.yaml"
    content = experience_file.read_text(encoding="utf-8")
    content += "  - id: exp-acme-1\n    tags: [backend]\n    text: {es: Otro, en: Other}\n"
    experience_file.write_text(content, encoding="utf-8")

    errors = run_validation(tmp_path)

    assert any("exp-acme-1" in e for e in errors)


def test_run_validation_catches_unknown_override_id(tmp_path):
    _write_minimal_repo(tmp_path)
    config_file = tmp_path / "applications" / "acme-2026-01-01" / "config.yaml"
    config_file.write_text(
        textwrap.dedent(
            """
            company: Acme
            profile: backend
            lang: es
            overrides:
              include_bullets: [ghost-id]
            """
        ),
        encoding="utf-8",
    )

    errors = run_validation(tmp_path)

    assert any("ghost-id" in e for e in errors)
