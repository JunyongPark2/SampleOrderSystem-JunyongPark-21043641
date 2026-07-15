import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MAIN_PY = REPO_ROOT / "main.py"


class CliResult:
    def __init__(self, process: subprocess.CompletedProcess, data_dir: Path):
        self.returncode = process.returncode
        self.stdout = process.stdout
        self.stderr = process.stderr
        self.data_dir = data_dir

    def read_json(self, filename: str):
        path = self.data_dir / filename
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def run_cli(tmp_path):
    def _run(inputs: list, timeout: float = 10.0, data_dir: Path = None) -> CliResult:
        if data_dir is None:
            data_dir = tmp_path / "data"
            data_dir.mkdir()
        stdin_text = "\n".join(inputs) + "\n"
        process = subprocess.run(
            [sys.executable, str(MAIN_PY)],
            input=stdin_text,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env={**os.environ, "SAMPLEORDER_DATA_DIR": str(data_dir)},
            timeout=timeout,
        )
        return CliResult(process, data_dir)

    return _run
