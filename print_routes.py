from app.fast_api_app import app
for route in app.routes:
    print(route.path, getattr(route, "methods", "WS"))
