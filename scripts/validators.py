from pathlib import Path


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
            if not isinstance(value, dict):
                continue
            for lang in ("es", "en"):
                if not value.get(lang):
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


def check_tag_filters_match(profile: dict, items: list[dict]) -> list[str]:
    errors = []
    profile_name = profile.get("name", profile.get("_source", "<unknown>"))
    for section in profile.get("sections") or []:
        tag_filter = section.get("tag_filter")
        if not tag_filter:
            continue
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
