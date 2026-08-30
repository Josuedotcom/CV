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
