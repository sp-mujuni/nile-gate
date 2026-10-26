FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 NILE_GATE_DB_PATH=/var/data/nile_gate.db
WORKDIR /app
COPY pyproject.toml README.md ./
COPY nile_gate ./nile_gate
RUN pip install --no-cache-dir .
RUN mkdir -p /var/data
EXPOSE 8000
CMD ["sh", "-c", "uvicorn nile_gate.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
