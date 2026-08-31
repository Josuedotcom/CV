def select_bullets(
    bullets: list[dict],
    tag_filter: list[str] | None,
    max_count: int | None,
    overrides: dict,
) -> list[dict]:
    excluded = set(overrides.get("exclude_bullets") or [])
    included_ids = set(overrides.get("include_bullets") or [])

    # Forced includes are an explicit user override, so they are never subject to
    # max_count truncation; only tag-matched bullets are trimmed to fit around them.
    forced = []
    filtered = []
    for bullet in bullets:
        if bullet["id"] in excluded:
            continue
        if bullet["id"] in included_ids:
            forced.append(bullet)
            continue
        matches_filter = tag_filter is None or bool(set(bullet.get("tags") or []) & set(tag_filter))
        if matches_filter:
            filtered.append(bullet)

    if max_count is not None:
        remaining = max(max_count - len(forced), 0)
        filtered = filtered[:remaining]

    return forced + filtered
