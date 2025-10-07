FROM python:3.11-slim

WORKDIR /app

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY src/ ./src/
COPY .env* ./

# Crea directory per dati e logs
RUN mkdir -p data logs

# Crea utente non-root per sicurezza
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Esponi la porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando di avvio
CMD ["python", "src/api.py"]