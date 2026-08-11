"""Smoke tests for the FastAPI app module."""


def test_health_importable() -> None:
    """The app module imports cleanly and exposes the FastAPI instance."""
    import app

    assert hasattr(app, "app")
