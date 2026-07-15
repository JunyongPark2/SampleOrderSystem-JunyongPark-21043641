import json
import os
from pathlib import Path


class JsonFileStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> list:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, records: list) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.path)
