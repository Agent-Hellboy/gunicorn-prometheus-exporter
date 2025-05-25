# Gevent Worker Example with Gunicorn

This example demonstrates using gevent-based workers with Gunicorn.

## Requirements
- Python 3.7+
- Dependencies listed in requirements.txt

## Installation
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Example
Start the Gunicorn server with gevent workers:
```bash
gunicorn -c gunicorn_config.py app:app
```

The application will be available at `http://localhost:8080`

## Endpoints
- `/`: Returns a simple greeting
- `/health`: Health check endpoint (returns 200 OK)

