# Decisión de arquitectura: framework de web app local

**Fecha:** decisión tomada en planificación de CV OSS
**Estado:** aceptada (T1)

## Decisión

Usar **Streamlit** como framework de la web app local que se distribuye con el repo para clonar.

## Alternativas evaluadas

| Framework | Ventajas | Desventajas para este caso |
|-----------|----------|---------------------------|
| **Streamlit** | Un solo archivo Python, `streamlit run app.py`, interfaz declarativa sin HTML/JS, ideal para apps de un solo propósito y usuarios no técnicos | Menos control fino sobre rutas HTTP que Flask/FastAPI |
| Flask | Ligero, estándar, control total | Necesita templates HTML, más código boilerplate, más fricción para no técnicos |
| FastAPI | Moderno, automático docs API | Necesita frontend separado (HTML/JS) o templates, más complejo para una app local simple |

## Justificación para CV Generator OSS

1. **Público objetivo mixto (técnicos + no técnicos):** Streamlit minimiza la fricción para usuarios generales — un comando y ya tienen la app en el navegador.
2. **Quickstart sencillo (S3):** `uv add streamlit` + `streamlit run` es todo lo que se necesita.
3. **Plantillas comunitarias (S5):** la lógica de generación (lectura de YAML, render Jinja2, compilado LaTeX) ya existe en `scripts/`; Streamlit solo añade una capa de UI delgada sobre ella.
4. **Generación de archivos locales:** Streamlit puede invocar `latexmk` vía `subprocess` y escribir `cv.tex`/`cv.pdf` en el disco de la máquina del usuario.

## Impacto en el repo

- Nueva dependencia: `streamlit` (agregar a `pyproject.toml` / `uv.lock`)
- Nueva carpeta: `web/` o `app/` con el punto de entrada de Streamlit
- Los scripts existentes (`generate.py`, `validate.py`, `renderer.py`) se reutilizan sin cambios
- CI debe incluir `streamlit` en `uv sync` y correr tests existentes
