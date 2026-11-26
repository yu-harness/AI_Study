FROM ghcr.io/astral-sh/uv:0.11.8-python3.12-trixie-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache -r /tmp/requirements.txt

COPY . /app/text_to_sql

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "text_to_sql.main:app_api", "--host", "0.0.0.0", "--port", "8000"]
