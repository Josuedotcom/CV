# Quickstart — Genera tu primer CV en 5 minutos

Esta guía es para quien clona el repositorio y quiere generar un CV sin tocar código.

## 1. Clona el repositorio

```bash
git clone https://github.com/<tu-usuario>/cv-generator.git
cd cv-generator
```

## 2. Instala dependencias

Necesitas [uv](https://docs.astral.sh/uv/) (gestor de Python):

```bash
uv sync
```

## 3. (Opcional pero recomendado) Instala LaTeX

Para compilar el PDF necesitas una distribución LaTeX con `latexmk`:

- Windows: [MiKTeX](https://miktex.org/)
- macOS: [MacTeX](https://tug.org/mactex/)
- Linux: `sudo apt-get install texlive-latex-extra latexmk`

Si no instalas LaTeX, aún puedes generar el archivo `.tex` y compilarlo después.

## 4. Ejecuta la app web local

```bash
streamlit run web/app.py
```

Se abrirá automáticamente en tu navegador (normalmente `http://localhost:8501`).

## 5. Genera tu CV

1. Elige **Crear nueva aplicación**.
2. Rellena: empresa, puesto, fecha, perfil, plantilla e idioma (`es` o `en`).
3. Pulsa **Crear y generar CV**.
4. Descarga `cv.tex` y `cv.pdf` desde los botones que aparecen.

Tu aplicación queda guardada en `applications/<empresa>-<fecha>/` como registro histórico de lo que generaste.

## Opción portable con Docker (sin instalar nada local)

```bash
docker build -t cv-generator .
docker run -p 8501:8501 --rm cv-generator
```

Después abrí `http://localhost:8501`. El contenedor trae Python 3.11, Streamlit, MiKTeX/TeX Live (`latexmk`) y tu repo todo junto.

## ¿Qué sigue?

- Edita `data/` para añadir tu experiencia, habilidades, educación, etc.
- Crea tu propio perfil en `profiles/` o edita `data-analyst.yaml`.
- Añade plantillas nuevas en `templates/` (formato `.tex.j2`).
- Lee `docs/superpowers/specs/2026-08-30-cv-generator-design.md` para entender cómo se estructuran los datos.

## Ayuda

Si algo falla, ejecuta primero `make validate` para revisar que tus archivos YAML están bien antes de generar.
