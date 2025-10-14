"""Test WSGI application for integration tests."""


def app(environ, start_response):
    """Simple WSGI application for testing."""
    path = environ.get("PATH_INFO", "/")

    if path == "/health":
        status = "200 OK"
        headers = [("Content-Type", "text/plain")]
        start_response(status, headers)
        return [b"OK"]
    else:
        status = "200 OK"
        headers = [("Content-Type", "text/plain")]
        start_response(status, headers)
        return [b"Hello, World!"]
