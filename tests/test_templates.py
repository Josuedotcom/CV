"""Smoke tests that render the REAL templates under templates/.

Every other template-touching test writes a throwaway .tex.j2 into tmp_path, so
nothing else in the suite would notice a syntax break (a bad \\BLOCK/\\VAR, or a
variable that StrictUndefined rejects) shipped in templates/ats.tex.j2 or
templates/visual.tex.j2. These tests render them for real.

They do NOT prove the compiled PDF is correct -- that needs an actual latexmk run
and text extraction, which is out of scope for a unit test.
"""

from pathlib import Path

import pytest

from scripts.renderer import render_template

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"


def _context() -> dict:
    """A representative context, shaped exactly like build_context() output."""
    return {
        "lang": "es",
        "company": "Sample Company",
        "role_applied": "Backend Engineer",
        "experience": [
            {
                "company": "Empresa de Ejemplo",
                "role": "Desarrollador Backend",
                "start_date": "2022-01",
                "end_date": "present",
                "bullets": [
                    "Lideré la migración a microservicios, reduciendo el deploy 40%.",
                    "Mentoreé a 3 desarrolladores junior.",
                ],
            }
        ],
        "skills": [{"name": "Python"}, {"name": "PostgreSQL"}],
        "projects": [{"name": "Proyecto", "description": "Una descripción."}],
        "education": [{"name": "Universidad de Ejemplo", "degree": "Ingeniería en Sistemas"}],
        "certifications": [
            {
                "name": "Certificación de Ejemplo",
                "issuer": "Sample Issuer",
                "date": "2023-05",
                "badge_image": "../../assets/badges/sample-badge.png",
            }
        ],
    }


@pytest.mark.parametrize("template_name", ["ats.tex.j2", "visual.tex.j2"])
def test_real_template_renders_full_context(template_name):
    result = render_template(TEMPLATES_DIR, template_name, _context())

    assert r"\begin{document}" in result
    assert r"\end{document}" in result
    assert "Desarrollador Backend" in result
    assert "Empresa de Ejemplo" in result
    assert "Lideré la migración" in result
    assert "Python, PostgreSQL" in result
    # Accented source text must survive rendering as literal UTF-8, unescaped.
    assert "Mentoreé" in result


@pytest.mark.parametrize("template_name", ["ats.tex.j2", "visual.tex.j2"])
def test_real_template_renders_with_all_sections_empty(template_name):
    context = _context()
    for key in ("experience", "skills", "projects", "education", "certifications"):
        context[key] = []

    result = render_template(TEMPLATES_DIR, template_name, context)

    assert r"\begin{document}" in result
    assert r"\end{document}" in result


def test_real_ats_template_renders_education_and_projects():
    result = render_template(TEMPLATES_DIR, "ats.tex.j2", _context())

    assert "Ingeniería en Sistemas" in result
    assert "Universidad de Ejemplo" in result
    assert "Una descripción." in result


def test_real_visual_template_renders_certification_badge():
    result = render_template(TEMPLATES_DIR, "visual.tex.j2", _context())

    assert r"\includegraphics" in result
    assert "../../assets/badges/sample-badge.png" in result
    assert "Certificación de Ejemplo" in result
    assert "Sample Issuer" in result


def test_real_visual_template_omits_badge_when_certification_has_none():
    context = _context()
    context["certifications"] = [
        {
            "name": "Sin Badge",
            "issuer": "Sample Issuer",
            "date": "2024-01",
            "badge_image": None,
        }
    ]

    result = render_template(TEMPLATES_DIR, "visual.tex.j2", context)

    assert r"\includegraphics" not in result
    assert "Sin Badge" in result
