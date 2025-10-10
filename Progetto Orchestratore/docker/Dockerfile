# ==== 1. Base image ====
FROM python:3.11-slim

# ==== 2. Env setup ====
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ==== 3. System deps ====
RUN apt-get update && apt-get install -y build-essential libxml2-dev libxslt1-dev && rm -rf /var/lib/apt/lists/*

# ==== 4. Copy project ====
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY .env .env
COPY outputs/ outputs/

# ==== 5. Entrypoint ====
CMD ["uvicorn", "orchestrator.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]