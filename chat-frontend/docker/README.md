# AWS AgentCore Backend - Deployment su Raspberry Pi

Questa guida spiega come deployare il backend AWS AgentCore su un Raspberry Pi utilizzando Docker.

## Prerequisiti

- Raspberry Pi 4 (consigliato) con Raspberry Pi OS (64-bit)
- Docker e Docker Compose installati
- Credenziali AWS configurate
- Connessione internet stabile

## Installazione Docker su Raspberry Pi

Se Docker non è già installato:

```bash
# Aggiorna il sistema
sudo apt-get update && sudo apt-get upgrade -y

# Installa Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Aggiungi l'utente al gruppo docker
sudo usermod -aG docker $USER

# Installa Docker Compose
sudo apt-get install -y docker-compose

# Riavvia per applicare i cambiamenti
sudo reboot
```

## Configurazione AWS

### Opzione 1: Variabili d'ambiente

Crea un file `.env` nella cartella `docker/`:

```bash
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_SESSION_TOKEN=your_session_token  # Opzionale
AWS_REGION=us-east-1
```

### Opzione 2: AWS CLI Profile

Configura AWS CLI sul Raspberry Pi:

```bash
# Installa AWS CLI
sudo apt-get install -y awscli

# Configura le credenziali
aws configure
```

Le credenziali verranno montate automaticamente nel container tramite il volume `~/.aws`.

## Build e Deploy

### 1. Clona il repository

```bash
cd ~
git clone <repository-url> aws-agentcore
cd aws-agentcore
git checkout rpi
cd chat-frontend/docker
```

### 2. Build dell'immagine

```bash
# Build per architettura ARM64
docker-compose build
```

### 3. Avvia il container

```bash
# Avvia in background
docker-compose up -d

# Visualizza i log
docker-compose logs -f backend
```

### 4. Verifica lo stato

```bash
# Controlla che il container sia in esecuzione
docker ps

# Test dell'endpoint
curl http://localhost:5000/health
```

## Gestione del Container

```bash
# Stop del container
docker-compose stop

# Start del container
docker-compose start

# Restart del container
docker-compose restart

# Stop e rimozione del container
docker-compose down

# Visualizza i log in tempo reale
docker-compose logs -f backend

# Accedi al container
docker-compose exec backend /bin/bash
```

## Ottimizzazioni per Raspberry Pi

### 1. Limitare l'uso della memoria

Modifica il `docker-compose.yml` aggiungendo:

```yaml
services:
  backend:
    mem_limit: 512m
    mem_reservation: 256m
```

### 2. Configurare il swap

Se il Raspberry Pi ha poca RAM:

```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Imposta CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 3. Avvio automatico al boot

```bash
# Abilita Docker all'avvio
sudo systemctl enable docker

# Aggiungi al crontab
crontab -e
# Aggiungi questa riga:
@reboot sleep 30 && cd /home/pi/aws-agentcore/chat-frontend/docker && docker-compose up -d
```

## Monitoraggio

### Monitorare le risorse

```bash
# Statistiche del container in tempo reale
docker stats aws-agentcore-backend

# Uso del disco
docker system df
```

### Log di sistema

```bash
# Ultimi 100 log del container
docker-compose logs --tail=100 backend

# Salva i log in un file
docker-compose logs backend > backend.log
```

## Troubleshooting

### Il container non si avvia

```bash
# Controlla i log
docker-compose logs backend

# Verifica le credenziali AWS
docker-compose exec backend env | grep AWS
```

### Problemi di memoria

```bash
# Pulisci immagini e container non utilizzati
docker system prune -a

# Riduci la memoria del container nel docker-compose.yml
```

### Errori di connessione AWS

```bash
# Verifica la connettività
docker-compose exec backend python -c "import boto3; print(boto3.client('sts').get_caller_identity())"
```

## Accesso dal Browser

Una volta avviato il container, il backend sarà accessibile da:

- `http://<raspberry-pi-ip>:5000` - dalla rete locale
- `http://localhost:5000` - dal Raspberry Pi stesso

Per accedere dall'esterno della rete locale, configura il port forwarding sul router.

## Aggiornamento

```bash
cd ~/aws-agentcore/chat-frontend/docker
git pull origin rpi
docker-compose down
docker-compose build
docker-compose up -d
```

## Note di Sicurezza

1. Non esporre mai il backend direttamente su Internet senza autenticazione
2. Usa HTTPS in produzione con un reverse proxy (nginx/traefik)
3. Proteggi il file `.env` con permessi appropriati: `chmod 600 .env`
4. Aggiorna regolarmente le immagini Docker: `docker-compose pull && docker-compose up -d`

## Supporto

Per problemi o domande, consulta i log del container:

```bash
docker-compose logs -f backend
```
