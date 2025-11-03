# syntax=docker/dockerfile:1

# ---- 1) Base image ----
# Use a small Python image that still has wheels support for SciPy / scikit-learn.
FROM python:3.11-slim

# ---- 2) Environment settings ----
# Avoid writing .pyc files, ensure unbuffered logs, disable pip cache, and set Python path.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

# ---- 3) Working directory ----
# All subsequent commands will run from /app
WORKDIR /app

# ---- 4) Requirements first (better layer caching) ----
# Copy only requirements to leverage Docker layer caching
COPY requirements.txt ./requirements.txt

# ---- 5) Install dependencies ----
# Upgrade pip and install production requirements
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ---- 6) Copy application code ----
# Copy the minimal runtime code: src/ for app + config/ for env files/templates
# Other folders (data/models/logs) are created below and typically mounted as volumes.
COPY src ./src
COPY config ./config

# ---- 7) Create runtime directories ----
# Pre-create folders the app may expect; they can also be mounted as volumes at runtime.
RUN mkdir -p /app/models /app/data /app/logs

# ---- 8) Expose API port ----
# FastAPI/Uvicorn default port
EXPOSE 8000

# ---- 9) Default command ----
# Start the ASGI server pointing to FastAPI app (src/app.py -> app)
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]