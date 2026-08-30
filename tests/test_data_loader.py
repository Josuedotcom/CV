from scripts.data_loader import load_yaml_file, load_yaml_dir


def test_load_yaml_file_parses_content_and_tags_source(tmp_path):
    file_path = tmp_path / "sample.yaml"
    file_path.write_text("name: {es: Hola, en: Hello}\n", encoding="utf-8")

    result = load_yaml_file(file_path)

    assert result["name"]["es"] == "Hola"
    assert result["_source"] == str(file_path)


def test_load_yaml_dir_loads_all_yaml_files_sorted(tmp_path):
    (tmp_path / "b.yaml").write_text("id: b\n", encoding="utf-8")
    (tmp_path / "a.yaml").write_text("id: a\n", encoding="utf-8")

    result = load_yaml_dir(tmp_path)

    assert [entry["id"] for entry in result] == ["a", "b"]
