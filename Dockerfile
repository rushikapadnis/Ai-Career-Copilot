FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=120
ENV PIP_RETRIES=10
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY agents ./agents
COPY mcp_servers ./mcp_servers
COPY migrations ./migrations
COPY alembic.ini .
COPY data ./data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
