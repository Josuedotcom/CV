# Contribuir a CV Generator

Gracias por contribuir. Este proyecto es un generador de CV basado en YAML + Jinja2/LaTeX. Toda contribución debe pasar los tests y la validación existente.

## Cómo empezar

1. Clona el repo: `git clone https://github.com/<tu-usuario>/cv-generator.git`
2. Instala dependencias: `uv sync`
3. Ejecuta los tests: `uv run pytest`
4. Ejecuta la validación: `make validate`

## Convenciones de código

- Usa convencional commits (`feat:`, `fix:`, `chore:`, `test:`, `docs:`).
- Cada función de `scripts/` recibe `repo_root: Path` (nada de rutas globales hardcodeadas), para que sea testeable con `tmp_path`.
- No añadas dependencias nuevas sin consultar primero (el stack es intencionalmente pequeño: PyYAML, Jinja2, pytest, Streamlit).

## Convención de plantillas (`.tex.j2`)

Las plantillas viven en `templates/` y se usan así:

```yaml
template: <nombre-sin-ext>
```

### Requisitos de una plantilla nueva

1. **Extensión**: `<nombre>.tex.j2` dentro de `templates/`.
2. **StrictUndefined**: el entorno Jinja2 usa `StrictUndefined`, así que cualquier variable faltante falla la generación (nunca renderiza en blanco).
3. **Variables disponibles** (según el profile/section que seleccione el usuario):
   - `name`, `title`, `email`, `phone`, `summary`
   - `experience`: lista de `{role, company, start_date, end_date, bullets: [str]}`
   - `skills`: lista de `{name}`
   - `projects`: lista de `{name, description}`
   - `education`: lista de `{degree, name}`
   - `certifications`: lista de `{name, issuer, date, badge_image}`
   - `company`, `role_applied` (del `config.yaml` de la aplicación)
4. **Filtro `|latex`**: usa `{{ variable|latex }}` para escapar caracteres especiales de LaTeX.
5. **Sintaxis de bloques**: usa `\BLOCK{...}` / `\VAR{...}` (no la sintaxis `{% %}` / `{{ }}` por defecto de Jinja2, para evitar conflictos con LaTeX).
6. **ATS-safe**: si tu plantilla se anuncia como ATS-safe, manténla de una sola columna, sin tablas, sin `\multicols` y sin imágenes.

### Ejemplo de plantilla contribuida

Véase `templates/modern.tex.j2` como plantilla de referencia para contribuciones.

## Añadir una plantilla nueva

1. Crea `templates/<tu-plantilla>.tex.j2` siguiendo la convención arriba.
2. Añade un ejemplo en `applications/` que la use (opcional pero recomendado).
3. Ejecuta `make validate` y `uv run pytest` para que todo pase.
4. Abre un PR describiendo qué hace la plantilla y para qué tipo de CV es útil.

## Reportar bugs / sugerir mejoras

Abre un issue describiendo el problema, los pasos para reproducirlo y, si aplica, el archivo YAML o plantilla que lo provoca.

## Licencia

Véase `LICENSE`.
