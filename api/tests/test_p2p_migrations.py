"""Clean installations and rollback use Alembic without application side effects."""

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect


def test_p2p_migration_upgrade_and_rollback(tmp_path):
    database = tmp_path / "migrations.db"
    url = f"sqlite:///{database}"
    api_root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "DATABASE_URL": url}

    def migrate(*arguments):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *arguments], cwd=api_root, env=env,
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr

    migrate("upgrade", "head")
    engine = create_engine(url)
    try:
        assert "p2p_services" in inspect(engine).get_table_names()
        columns = {item["name"] for item in inspect(engine).get_columns("p2p_services")}
        assert {"uid", "secret_key", "fallback_enabled", "local_ip", "local_port"} <= columns
        migrate("downgrade", "-1")
        assert "p2p_services" not in inspect(engine).get_table_names()
        assert "published_services" in inspect(engine).get_table_names()
        migrate("upgrade", "head")
        assert "p2p_services" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
