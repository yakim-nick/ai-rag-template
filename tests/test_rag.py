def test_health_importable():
    # smoke test: app module imports and exposes FastAPI app
    import app

    assert hasattr(app, "app")
