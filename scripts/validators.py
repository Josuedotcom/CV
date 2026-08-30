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
