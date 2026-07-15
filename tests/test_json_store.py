from sampleorder.json_store import JsonFileStore


def test_load_returns_empty_list_when_file_missing(tmp_path):
    store = JsonFileStore(tmp_path / "missing.json")
    assert store.load() == []


def test_save_then_load_roundtrips_data(tmp_path):
    store = JsonFileStore(tmp_path / "data.json")
    records = [{"a": 1}, {"b": 2}]
    store.save(records)
    assert store.load() == records


def test_save_does_not_leave_tmp_file(tmp_path):
    path = tmp_path / "data.json"
    store = JsonFileStore(path)
    store.save([{"a": 1}])
    assert not path.with_suffix(".tmp").exists()
    assert path.exists()
