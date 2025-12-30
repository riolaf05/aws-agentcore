# Dockerfile per Raspberry Pi (ARM architecture)
# Base image ottimizzata per ARM64
FROM python:3.11-slim-bookworm

# Metadata
LABEL maintainer="your-email@example.com"
LABEL description="AWS AgentCore Backend for Raspberry Pi"

# Imposta variabili d'ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Crea directory di lavoro
WORKDIR /app

# Installa dipendenze di sistema necessarie
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY backend.py .
COPY index.html .
COPY app.js .
COPY style.css .
COPY modal-styles.css .
COPY cognito-config.js .

# Crea un utente non-root per sicurezza
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Esponi la porta 5000
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health').read()"

# Comando di avvio
CMD ["python", "-u", "backend.py"]
