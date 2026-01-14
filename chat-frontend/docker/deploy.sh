#!/bin/bash
# Script di deploy rapido per Raspberry Pi

set -e

echo "========================================"
echo "AWS AgentCore Backend - Deploy su RPi"
echo "========================================"

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funzione per stampare messaggi
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verifica Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker non è installato!"
    echo "Installare Docker con: curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh"
    exit 1
fi

# Verifica Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose non è installato!"
    echo "Installare Docker Compose con: sudo apt-get install -y docker-compose"
    exit 1
fi

# Vai alla directory docker
cd "$(dirname "$0")"

# Verifica file .env
if [ ! -f .env ]; then
    print_warn "File .env non trovato!"
    if [ -f .env.example ]; then
        print_info "Copiando .env.example in .env..."
        cp .env.example .env
        print_warn "ATTENZIONE: Modifica il file .env con le tue credenziali AWS prima di continuare!"
        print_info "Apri .env con: nano .env"
        exit 1
    else
        print_error "File .env.example non trovato!"
        exit 1
    fi
fi

# Menu
echo ""
echo "Scegli un'azione:"
echo "1) Build dell'immagine Docker"
echo "2) Avvia il container"
echo "3) Stop del container"
echo "4) Restart del container"
echo "5) Visualizza i log"
echo "6) Verifica lo stato"
echo "7) Rimuovi tutto (container e immagini)"
echo "8) Deploy completo (build + start)"
echo "0) Esci"
echo ""

read -p "Selezione: " choice

case $choice in
    1)
        print_info "Building dell'immagine Docker..."
        docker-compose build
        print_info "Build completata!"
        ;;
    2)
        print_info "Avvio del container..."
        docker-compose up -d
        print_info "Container avviato!"
        echo ""
        print_info "Verifica lo stato con: docker ps"
        print_info "Backend disponibile su: http://$(hostname -I | awk '{print $1}'):5000"
        ;;
    3)
        print_info "Stopping del container..."
        docker-compose stop
        print_info "Container fermato!"
        ;;
    4)
        print_info "Restart del container..."
        docker-compose restart
        print_info "Container riavviato!"
        ;;
    5)
        print_info "Visualizzazione log (Ctrl+C per uscire)..."
        docker-compose logs -f backend
        ;;
    6)
        print_info "Stato del sistema:"
        echo ""
        echo "=== Container in esecuzione ==="
        docker ps
        echo ""
        echo "=== Health check ==="
        if curl -s -f http://localhost:5000/health > /dev/null; then
            print_info "Backend è raggiungibile!"
            curl -s http://localhost:5000/health | python -m json.tool
        else
            print_error "Backend non risponde!"
        fi
        echo ""
        echo "=== Statistiche risorse ==="
        docker stats --no-stream aws-agentcore-backend 2>/dev/null || print_warn "Container non in esecuzione"
        ;;
    7)
        print_warn "Rimozione di tutti i container e immagini..."
        read -p "Sei sicuro? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            docker-compose down
            docker rmi $(docker images -q aws-agentcore*) 2>/dev/null || true
            print_info "Pulizia completata!"
        else
            print_info "Operazione annullata"
        fi
        ;;
    8)
        print_info "Deploy completo in corso..."
        echo ""
        print_info "Step 1: Building immagine..."
        docker-compose build
        echo ""
        print_info "Step 2: Avvio container..."
        docker-compose up -d
        echo ""
        print_info "Deploy completato!"
        echo ""
        print_info "Backend disponibile su: http://$(hostname -I | awk '{print $1}'):5000"
        echo ""
        print_info "Verifica lo stato con:"
        echo "  curl http://localhost:5000/health"
        ;;
    0)
        print_info "Uscita..."
        exit 0
        ;;
    *)
        print_error "Scelta non valida!"
        exit 1
        ;;
esac

echo ""
print_info "Operazione completata!"
