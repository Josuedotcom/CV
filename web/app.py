"""CV Generator — local web app.

Run with:

    streamlit run web/app.py

This is a thin Streamlit UI over the existing generation pipeline in
``scripts/generate.py``. It lets you pick or create an application, choose a
profile, template and language, and generate ``cv.tex`` + ``cv.pdf`` locally
without touching a terminal.
"""

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.generate import generate  # noqa: E402

APPS_DIR = REPO_ROOT / "applications"
PROFILES_DIR = REPO_ROOT / "profiles"
TEMPLATES_DIR = REPO_ROOT / "templates"


def list_applications() -> list[str]:
    if not APPS_DIR.exists():
        return []
    return sorted(
        d.name for d in APPS_DIR.iterdir() if d.is_dir() and (d / "config.yaml").exists()
    )


def list_profiles() -> list[str]:
    if not PROFILES_DIR.exists():
        return []
    return sorted(p.stem for p in PROFILES_DIR.glob("*.yaml"))


def list_templates() -> list[str]:
    if not TEMPLATES_DIR.exists():
        return []
    return sorted(
        t.name.replace(".tex.j2", "")
        for t in TEMPLATES_DIR.glob("*.tex.j2")
    )


def app_name_from_inputs(company: str, date_str: str) -> str:
    safe = "".join(c if c.isalnum() or c in "- " else "-" for c in company.strip())
    safe = safe.strip().replace(" ", "-").lower()
    return f"{safe}-{date_str}"


def main() -> None:
    st.set_page_config(page_title="CV Generator", page_icon="\U0001F4BB", layout="centered")
    st.title("\U0001F4BB CV Generator")
    st.caption("Genera tu CV (cv.tex + cv.pdf) desde el navegador, en tu máquina local.")

    apps = list_applications()
    profiles = list_profiles()
    templates = list_templates()

    if not profiles:
        st.error("No se encontraron perfiles en `profiles/`.")
        st.stop()
    if not templates:
        st.error("No se encontraron plantillas en `templates/`.")
        st.stop()

    mode = st.radio("¿Qué quieres hacer?", ["Crear nueva aplicación", "Usar una existente"], horizontal=True)

    app_name = None
    config = {}

    if mode == "Usar una existente" and apps:
        app_name = st.selectbox("Selecciona una aplicación", apps)
        if app_name:
            import yaml
            config = yaml.safe_load((APPS_DIR / app_name / "config.yaml").read_text(encoding="utf-8"))
    else:
        with st.form("new_app_form"):
            st.subheader("Datos de la aplicación")
            company = st.text_input("Empresa", placeholder="Ej. Acme Corp")
            role = st.text_input("Puesto solicitado", placeholder="Ej. Analista de Datos")
            date_str = st.date_input("Fecha").isoformat() if st.checkbox("Usar fecha de hoy", value=True) else st.text_input("Fecha (YYYY-MM-DD)", value="2026-01-01")
            profile = st.selectbox("Perfil", profiles, index=0)
            template = st.selectbox("Plantilla", templates, index=0)
            lang = st.selectbox("Idioma", ["es", "en"], index=0)
            notes = st.text_area("Notas (opcional)", placeholder="Notas sobre esta aplicación")
            submitted = st.form_submit_button("Crear y generar CV")

            if submitted:
                if not company or not role:
                    st.error("Empresa y puesto son obligatorios.")
                    st.stop()
                app_name = app_name_from_inputs(company, date_str)
                config = {
                    "company": company,
                    "role_applied": role,
                    "date": date_str,
                    "profile": profile,
                    "template": template,
                    "lang": lang,
                    "notes": notes or "",
                }

    if app_name and config:
        st.divider()
        st.subheader(f"Aplicación: {app_name}")
        col1, col2 = st.columns(2)
        with col1:
            compile_pdf = st.checkbox("Compilar PDF (necesita LaTeX/latexmk)", value=True)
        with col2:
            generate_btn = st.button("Generar CV", type="primary")

        if generate_btn:
            app_dir = APPS_DIR / app_name
            app_dir.mkdir(parents=True, exist_ok=True)
            (app_dir / "config.yaml").write_text(
                __import__("yaml").dump(config, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            try:
                tex_path = generate(app_name, repo_root=REPO_ROOT, compile=compile_pdf)
                suffix = "cv.tex y cv.pdf" if compile_pdf else "cv.tex"
                st.success(f"Generado: {tex_path.parent.name}/{suffix}")
                if compile_pdf:
                    pdf_path = app_dir / "cv.pdf"
                    if pdf_path.exists():
                        st.download_button(
                            "Descargar cv.pdf",
                            data=pdf_path.read_bytes(),
                            file_name="cv.pdf",
                            mime="application/pdf",
                        )
                tex_path_obj = app_dir / "cv.tex"
                if tex_path_obj.exists():
                    st.download_button(
                        "Descargar cv.tex",
                        data=tex_path_obj.read_text(encoding="utf-8"),
                        file_name="cv.tex",
                        mime="text/plain",
                    )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Error generando el CV:\n\n{exc}")


if __name__ == "__main__":
    main()
