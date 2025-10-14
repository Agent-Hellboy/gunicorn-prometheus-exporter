FROM python:3.11-slim

WORKDIR /app
COPY test_app.py /app/

RUN pip install gunicorn

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "test_app:app"]
