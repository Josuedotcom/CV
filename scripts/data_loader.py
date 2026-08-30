from pathlib import Path

import yaml


def load_yaml_file(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data["_source"] = str(path)
    return data


def load_yaml_dir(dir_path: Path) -> list[dict]:
    return [load_yaml_file(path) for path in sorted(dir_path.glob("*.yaml"))]
