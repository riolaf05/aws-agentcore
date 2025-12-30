# Script PowerShell per test locale su Windows
# Simula il deployment prima di trasferirlo su Raspberry Pi

Write-Host "========================================"
Write-Host "Test Build Docker per Raspberry Pi"
Write-Host "========================================"

# Vai alla directory docker
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Verifica Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERRORE: Docker non è installato!" -ForegroundColor Red
    exit 1
}

# Verifica file .env
if (-not (Test-Path .env)) {
    Write-Host "ATTENZIONE: File .env non trovato!" -ForegroundColor Yellow
    if (Test-Path .env.example) {
        Write-Host "Copiando .env.example in .env..." -ForegroundColor Green
        Copy-Item .env.example .env
        Write-Host "ATTENZIONE: Modifica il file .env con le tue credenziali AWS!" -ForegroundColor Yellow
        exit 1
    }
}

# Menu
Write-Host ""
Write-Host "Scegli un'azione:"
Write-Host "1) Build dell'immagine Docker"
Write-Host "2) Test build (verifica sintassi Dockerfile)"
Write-Host "3) Visualizza struttura dell'immagine"
Write-Host "0) Esci"
Write-Host ""

$choice = Read-Host "Selezione"

switch ($choice) {
    1 {
        Write-Host "Building dell'immagine Docker..." -ForegroundColor Green
        docker-compose build
        Write-Host "Build completata!" -ForegroundColor Green
    }
    2 {
        Write-Host "Test della build..." -ForegroundColor Green
        docker build --no-cache -f Dockerfile -t test-rpi-backend ..
        Write-Host "Test completato!" -ForegroundColor Green
    }
    3 {
        Write-Host "Struttura dell'immagine:" -ForegroundColor Green
        docker images | Select-String "agentcore"
    }
    0 {
        Write-Host "Uscita..." -ForegroundColor Green
        exit 0
    }
    default {
        Write-Host "Scelta non valida!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Operazione completata!" -ForegroundColor Green
