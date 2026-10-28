"""Offline tools must be able to load settings and models without web startup."""

import os
import subprocess
import sys


def test_configuration_and_model_imports_do_not_create_database(tmp_path):
    database = tmp_path / "import.db"
    result = subprocess.run(
        [sys.executable, "-c", "from src.app.config import settings; from src.app.models import db_models"],
        env={**os.environ, "DATABASE_URL": f"sqlite:///{database}"},
        capture_output=True, timeout=20,
    )
    assert result.returncode == 0
    assert not database.exists()
