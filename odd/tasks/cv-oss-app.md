# CV Generator → App Open Source

**Goal:** Convertir el generador de CV personal en una app open source que terceros puedan clonar y usar localmente, con una web app que funcione en la máquina de quien baja el repo, plantillas comunitarias contribuibles y soporte bilingual ES/EN fijo.

**Decisiones de usuario (capturadas en planificación):**
- ENTREGA: "clone el repo pero lancemos una web app que funcione en local de la persona que baja el repo"
- PUBLICO: "Ambos" (desarrolladores/técnicos + usuarios generales)
- IDIOMAS: "Mantener ES/EN (bilingüe fijo)"
- FOCO OSS: "Plantillas comunitarias"

## Specs

S1: La app se distribuye como plantilla de repo GitHub para clonar (fork & use), no solo como paquete pip.
S2: Incluye una web app que funcione en local en la máquina de quien clona el repo (sin depender de hosting externo).
S3: Público objetivo: tanto desarrolladores/técnicos (YAML, terminal, Git) como usuarios generales (menos fricción, quickstart sencillo).
S4: Soporte de idiomas: ES/EN fijo (bilingüe `{es: ..., en: ...}` como hoy), sin tercer idioma ni multidioma abierto al inicio.
S5: Plantillas comunitarias: otros usuarios pueden contribuir nuevos diseños `.tex.j2` bajo `templates/`.
S6: Mantener validación existente (`make validate`) y CI de GitHub Actions (validate + pytest + build de PDFs).
S7: Cada aplicación sigue siendo un registro histórico (`config.yaml` + `cv.tex` + `cv.pdf` juntos).
S8: Agregar documentación de contribuyente (CONTRIBUTING, LICENSE, README actualizado para OSS).

## Tasks

T1 — S1/S2/S3: Investigar y elegir framework de web app local (Streamlit / Flask / FastAPI) y documentar la decisión — route: exploring — commit: docs/decision
T2 — S2: Prototipo de web app local que lea `data/`, `profiles/`, `templates/` y genere `cv.tex`/`cv.pdf` desde el navegador local — route: implementing — commit: web-app-prototype
T3 — S3: Añadir quickstart sencillo para usuarios no técnicos (un comando o paso claro para generar primer CV) — route: implementing — commit: quickstart
T4 — S4: Reafirmar y blindar el formato bilingüe ES/EN en validación y generación (no romper lo existente) — route: implementing — commit: validate-bilingual
T5 — S5: Establecer convención y carpeta para plantillas comunitarias + ejemplo de contribución (CONTRIBUTING + plantilla de ejemplo) — route: implementing — commit: community-templates
T6 — S6: Asegurar CI de GitHub Actions verde con la web app local incluida (tests + validate + build) — route: checking — commit: ci-green
T7 — S7/S8: LICENSE, CONTRIBUTING.md, README actualizado para lanzamiento OSS, renombrar/ajustar nombre del proyecto si aplica — route: implementing — commit: oss-docs
T8 — S1/S7: Ejemplo de aplicación completa (una `applications/`) como referencia para nuevos usuarios — route: implementing —commit: example-application

## Log

L1: Usuario pidió: "Si, quiero elevar el nivel y volver esto una app open source para hacer cv's, planifiquemos esto" — decisión de convertir el generador personal en app OSS clonable con web app local.
L2: Planificación capturada — ENTREGA: clonar repo + web app local; PUBLICO: Ambos; IDIOMAS: ES/EN fijo; FOCO OSS: Plantillas comunitarias.
