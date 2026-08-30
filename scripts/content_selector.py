def select_bullets(
    bullets: list[dict],
    tag_filter: list[str] | None,
    max_count: int | None,
    overrides: dict,
) -> list[dict]:
    excluded = set(overrides.get("exclude_bullets", []))
    included_ids = set(overrides.get("include_bullets", []))

    selected = []
    for bullet in bullets:
        if bullet["id"] in excluded:
            continue
        matches_filter = tag_filter is None or bool(set(bullet.get("tags", [])) & set(tag_filter))
        forced_include = bullet["id"] in included_ids
        if matches_filter or forced_include:
            selected.append(bullet)

    if max_count is not None:
        selected = selected[:max_count]

    return selected
