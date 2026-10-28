"""
Self Host Server API application
"""

__all__ = ["app"]


def __getattr__(name: str):
    # Importing models/settings for Alembic must not initialize the web app or
    # create tables before migrations run. Preserve `from src.app import app`.
    if name == "app":
        from .main import app

        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
