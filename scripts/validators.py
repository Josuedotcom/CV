from pathlib import Path

VALID_LANGS = ("es", "en")


def check_unique_ids(items: list[dict]) -> list[str]:
    seen: dict[str, str] = {}
    errors = []
    for item in items:
        item_id = item["id"]
        source = item.get("_source", "<unknown>")
        if item_id in seen:
            errors.append(
                f"Duplicate id '{item_id}' found in {source} "
                f"(first defined in {seen[item_id]})"
            )
        else:
            seen[item_id] = source
    return errors


def check_bilingual_fields(items: list[dict], field_names: list[str]) -> list[str]:
    errors = []
    for item in items:
        item_id = item.get("id", "<no id>")
        source = item.get("_source", "<unknown>")
        for field_name in field_names:
            value = item.get(field_name)
            if value is None:
                continue
            if not isinstance(value, dict):
                errors.append(
                    f"Item '{item_id}' in {source} field '{field_name}' "
                    f"no es un diccionario bilingual (es/en): {value!r}"
                )
                continue
            for key in value:
                if key not in ("es", "en"):
                    errors.append(
                        f"Item '{item_id}' in {source} field '{field_name}' "
                        f"tiene una clave de idioma no soportada: '{key}' "
                        f"(solo se permiten 'es' y 'en')"
                    )
            for lang in ("es", "en"):
                if lang not in value or not value[lang]:
                    errors.append(
                        f"Item '{item_id}' in {source} is missing '{lang}' "
                        f"text for field '{field_name}'"
                    )
    return errors


def check_override_ids_exist(application_config: dict, known_ids: set[str]) -> list[str]:
    errors = []
    overrides = application_config.get("overrides") or {}
    source = application_config.get("_source", "<unknown>")
    for key in ("include_bullets", "exclude_bullets"):
        for bullet_id in overrides.get(key, []):
            if bullet_id not in known_ids:
                errors.append(
                    f"{source}: overrides.{key} references unknown id '{bullet_id}'"
                )
    return errors


def check_application_config_valid(application_config: dict, repo_root: Path) -> list[str]:
    """Report typos in an application config before they become raw tracebacks."""
    errors = []
    source = application_config.get("_source", "<unknown>")

    lang = application_config.get("lang")
    if lang not in VALID_LANGS:
        errors.append(
            f"{source}: lang '{lang}' is not one of {list(VALID_LANGS)}"
        )

    profile = application_config.get("profile")
    if not profile or not (repo_root / "profiles" / f"{profile}.yaml").is_file():
        errors.append(
            f"{source}: profile '{profile}' has no matching file profiles/{profile}.yaml"
        )

    template = application_config.get("template")
    if not template or not (repo_root / "templates" / f"{template}.tex.j2").is_file():
        errors.append(
            f"{source}: template '{template}' has no matching file templates/{template}.tex.j2"
        )

    return errors


def check_tag_filters_match(profile: dict, items_by_type: dict[str, list[dict]]) -> list[str]:
    errors = []
    profile_name = profile.get("name") or profile.get("_source", "<unknown>")
    for section in profile.get("sections") or []:
        tag_filter = section.get("tag_filter")
        if not tag_filter:
            continue
        # A tag_filter only ever selects items of the section's own type, so an
        # unrelated type carrying the tag must not make the section look valid.
        # An unrecognised type has no items at all (generate() reports that case).
        items = items_by_type.get(section.get("type")) or []
        matches = any(set(item.get("tags") or []) & set(tag_filter) for item in items)
        if not matches:
            errors.append(
                f"Profile '{profile_name}' section '{section.get('type')}' "
                f"tag_filter {tag_filter} matches zero items"
            )
    return errors


def check_badge_images_exist(certifications: list[dict], repo_root: Path) -> list[str]:
    errors = []
    for cert in certifications:
        badge_path = cert.get("badge_image")
        if not badge_path:
            continue
        if not (repo_root / badge_path).is_file():
            errors.append(
                f"Certification '{cert.get('id')}' references missing badge image: {badge_path}"
            )
    return errors
