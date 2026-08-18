def test_api_route_modules_exist():
    from app.main import app
    paths = []
    for r in app.routes:
        if hasattr(r, "path"):
            paths.append(r.path)
        if hasattr(r, "original_router") and hasattr(r.original_router, "routes"):
            for sub in r.original_router.routes:
                if hasattr(sub, "path"):
                    paths.append(sub.path)
    assert any(p == "/tigers" or p.startswith("/tigers") for p in paths)

