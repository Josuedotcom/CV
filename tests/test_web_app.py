"""Tests de la web app local (web/app.py).

Solo verifican importación y funciones de listado; no inician el servidor
Streamlit (eso requeriría un navegador/entorno gráfico).
"""

from pathlib import Path

from web.app import list_applications, list_profiles, list_templates

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_web_app_imports_without_error():
    # Si esta línea falla, la web app tiene un error de importación y la CI
    # debe detenerse antes de entregar una app rota al usuario.
    import web.app  # noqa: F401


def test_list_profiles_returns_at_least_one():
    profiles = list_profiles()
    assert len(profiles) >= 1


def test_list_templates_returns_at_least_one():
    templates = list_templates()
    assert len(templates) >= 1


def test_list_applications_includes_existing():
    apps = list_applications()
    assert isinstance(apps, list)
