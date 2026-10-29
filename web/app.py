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

import yaml
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

    # Paso 1: Perfil (data/profile.yaml) — con instrucciones claras
    st.subheader("Paso 1: Crear tu perfil")
    st.info("**Estilo sugerido:** nombre breve; título profesional; resumen 2-4 líneas bilingüe (`es` / `en`); email profesional. Ejemplo rápido: `Ana García / Analista de Datos / ejemplo@email.com`.")
    with st.form("profile_form"):
        p_name = st.text_input("Nombre completo", placeholder="Ej. Ana García")
        p_title = st.text_input("Título profesional", placeholder="Ej. Analista de Datos")
        p_email = st.text_input("Email", placeholder="ejemplo@email.com")
        p_phone = st.text_input("Teléfono (opcional)", placeholder="+00 000 000 000")
        p_summary = st.text_area("Resumen (2-4 líneas, bilingüe `es` / `en`)", placeholder="Ej. Ingeniero con experiencia en SQL y dashboards / Engineer with SQL and dashboard experience")
        p_submit = st.form_submit_button("Guardar perfil")
        if p_submit:
            if not p_name or not p_title or not p_email:
                st.error("Nombre, título y email son obligatorios.")
            else:
                import yaml
                profile_path = REPO_ROOT / "data" / "profile.yaml"
                profile_path.parent.mkdir(parents=True, exist_ok=True)
                profile_path.write_text(
                    yaml.dump({
                        "name": {"es": p_name, "en": p_name},
                        "title": {"es": p_title, "en": p_title},
                        "email": p_email,
                        "phone": p_phone or "",
                        "summary": {"es": p_summary or "", "en": p_summary or ""},
                    }, allow_unicode=True, sort_keys=False),
                    encoding="utf-8",
                )
                st.success(f"Perfil guardado: {profile_path}")

    # Paso 2: Experiencia (data/experience/*.yaml) — con instrucciones claras
    st.subheader("Paso 2: Crear tu experiencia")
    st.info("**Estilo sugerido:** empresa y rol breves; bullets con `id` único, `tags`, `text: {es, en}`. Menciona resultados cuantificables (`reduje tiempos 20%`). Ejemplo: `tags: [data-analyst]`, `text: {es: Creé dashboards, en: Built dashboards}`.")
    with st.form("experience_form"):
        e_company = st.text_input("Empresa", placeholder="Ej. Empresa Ejemplo")
        e_role = st.text_input("Rol", placeholder="Ej. Analista de Datos")
        e_start = st.text_input("Fecha de inicio (YYYY-MM-DD)", placeholder="2025-01-01")
        e_end = st.text_input("Fecha de fin (opcional, YYYY-MM-DD)", placeholder="2025-12-31")
        e_bullet_es = st.text_area("Experiencia — texto español", placeholder="Ej. Analicé datos con SQL; creé dashboards en Power BI.")
        e_bullet_en = st.text_area("Experiencia — texto inglés", placeholder="Ej. Analyzed data with SQL; built Power BI dashboards.")
        e_tags = st.text_input("Tags (separados por comas, ej. ejemplo, backend)", placeholder="ejemplo")
        e_submit = st.form_submit_button("Guardar experiencia")
        if e_submit:
            if not e_company or not e_role or not e_start:
                st.error("Empresa, rol y fecha de inicio son obligatorios.")
            else:
                safe_name = "".join(c if c.isalnum() or c == "-" else "-" for c in e_company.strip()).lower().replace(" ", "-")
                exp_file = REPO_ROOT / "data" / "experience" / f"{safe_name}.yaml"
                exp_file.parent.mkdir(parents=True, exist_ok=True)
                tags = [t.strip() for t in e_tags.split(",") if t.strip()] or ["ejemplo"]
                exp_file.write_text(
                    yaml.dump({
                        "company": {"es": e_company, "en": e_company},
                        "role": {"es": e_role, "en": e_role},
                        "start_date": e_start,
                        "end_date": e_end or "",
                        "bullets": [
                            {
                                "id": f"exp-{safe_name}-1",
                                "tags": tags,
                                "text": {"es": e_bullet_es, "en": e_bullet_en},
                            }
                        ],
                    }, allow_unicode=True, sort_keys=False),
                    encoding="utf-8",
                )
                st.success(f"Experiencia guardada: {exp_file}")

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
            st.info("**Estilo de aplicación:** empresa real; rol aplicado; perfil = el creado en Paso 1 (`ejemplo` o tu propio); plantilla `ats` (ATS) o `visual`; idioma `es`/`en`; nota opcional.")
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
