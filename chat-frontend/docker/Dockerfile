# Dockerfile per Ubuntu (AMD64 architecture)
# Base image Ubuntu con Python
FROM ubuntu:22.04

# Metadata
LABEL maintainer="your-email@example.com"
LABEL description="AWS AgentCore Backend for Ubuntu AMD64"

# Imposta variabili d'ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Crea directory di lavoro
WORKDIR /app

# Installa Python e dipendenze di sistema necessarie
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Copia requirements e installa dipendenze Python
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione dal parent directory
COPY ../backend.py .
COPY ../index.html .
COPY ../app.js .
COPY ../style.css .
COPY ../modal-styles.css .
COPY ../cognito-config.js .
COPY ../favicon-robot.svg .

# Crea un utente non-root per sicurezza
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Esponi la porta 5000
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Comando di avvio
CMD ["python3", "-u", "backend.py"]
