"""Test WSGI application for system tests."""


def app(environ, start_response):
    """Simple WSGI application for testing."""
    status = "200 OK"
    headers = [("Content-Type", "text/plain")]
    start_response(status, headers)
    return [b"Hello, World!"]
