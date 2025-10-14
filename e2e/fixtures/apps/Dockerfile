FROM python:3.11-slim

WORKDIR /app
COPY test_app.py /app/

RUN pip install gunicorn

EXPOSE 8088
CMD ["gunicorn", "--bind", "0.0.0.0:8088", "--workers", "2", "test_app:app"]
