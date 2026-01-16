# Build stage
FROM public.ecr.aws/amazonlinux/amazonlinux:2023 AS builder

# Installa Python e dipendenze di build
RUN yum install -y python3.11 python3.11-pip gcc python3.11-devel && \
    yum clean all && \
    rm -rf /var/cache/yum

# Crea un ambiente virtuale
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copia e installa le dipendenze
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Runtime stage
FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# Installa solo il runtime Python
RUN yum install -y python3.11 && \
    yum clean all && \
    rm -rf /var/cache/yum

# Copia l'ambiente virtuale dallo stage di build
COPY --from=builder /opt/venv /opt/venv

# Imposta il PATH e le variabili d'ambiente
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Crea la directory di lavoro
WORKDIR /app

# Copia il codice sorgente
COPY . /app/

# Esponi la porta per l'agente
EXPOSE 8080

# Comando di avvio
CMD ["python3.11", "agent.py"]
